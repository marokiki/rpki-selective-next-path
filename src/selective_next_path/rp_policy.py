from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .result_io import write_json
from .semantics import canonical_json, compare_payloads, payload_digests, semantic_digest
from .state import ComparisonScope, SemanticPayload


@dataclass
class RPTransitionState:
    scope_id: str
    accepted_next_ta_id: str
    highest_transition_sequence: int = 0
    staged: bool = False
    activated: bool = False
    retired: bool = False
    last_resource_digest: str | None = None
    last_vrp_digest: str | None = None
    last_aspa_digest: str | None = None
    last_child_delegation_digest: str | None = None
    last_transition_digest: str | None = None


class RPTransitionPolicy:
    def __init__(self, path: Path, state: RPTransitionState):
        self.path = path
        self.state = state

    @classmethod
    def create(cls, path: Path, scope_id: str, accepted_next_ta_id: str) -> "RPTransitionPolicy":
        policy = cls(path, RPTransitionState(scope_id, accepted_next_ta_id))
        policy.save()
        return policy

    @classmethod
    def load(cls, path: Path) -> "RPTransitionPolicy":
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls(path, RPTransitionState(**raw["state"]))

    def save(self) -> None:
        write_json(self.path, {"schema_version": 1, "warning": "EXPERIMENTAL / NOT FOR PRODUCTION", "state": asdict(self.state)})

    def _guard(self, sequence: int, transition: dict[str, Any]) -> dict[str, Any] | None:
        digest = semantic_digest(transition)
        if sequence < self.state.highest_transition_sequence:
            return {"accepted": False, "reason": "SEQUENCE_REPLAY"}
        if sequence == self.state.highest_transition_sequence and sequence != 0:
            reason = "IDEMPOTENT_TRANSITION" if digest == self.state.last_transition_digest else "SEQUENCE_CONFLICT"
            return {"accepted": reason == "IDEMPOTENT_TRANSITION", "reason": reason}
        return None

    def _accept_transition(self, sequence: int, transition: dict[str, Any]) -> None:
        self.state.highest_transition_sequence = sequence
        self.state.last_transition_digest = semantic_digest(transition)

    def stage(self, sequence: int, ta_id: str, current: SemanticPayload, candidate: SemanticPayload, scope: ComparisonScope, valid_next_path: bool) -> dict[str, Any]:
        transition = {"action": "stage", "sequence": sequence, "ta_id": ta_id, "current": asdict(current), "candidate": asdict(candidate), "scope": asdict(scope), "valid_next_path": valid_next_path}
        guarded = self._guard(sequence, transition)
        if guarded:
            return guarded
        if ta_id != self.state.accepted_next_ta_id:
            return {"accepted": False, "reason": "NEXT_TA_REPLACEMENT_FORBIDDEN"}
        if self.state.activated or self.state.retired:
            return {"accepted": False, "reason": "STATE_ROLLBACK"}
        if not valid_next_path:
            return {"accepted": False, "reason": "INVALID_NEXT_PARENT_PATH"}
        equivalent, reason, _ = compare_payloads(current, candidate, scope)
        if not equivalent:
            return {"accepted": False, "reason": reason.value}
        self._accept_transition(sequence, transition)
        digests = payload_digests(candidate)
        self.state.staged = True
        self.state.last_resource_digest = digests["resources"]
        self.state.last_vrp_digest = digests["vrps"]
        self.state.last_aspa_digest = digests["aspas"]
        self.state.last_child_delegation_digest = digests["child_delegations"]
        self.save()
        return {"accepted": True, "reason": "NEXT_OUTPUT_STAGED"}

    def activate(self, sequence: int) -> dict[str, Any]:
        transition = {"action": "activate", "sequence": sequence}
        guarded = self._guard(sequence, transition)
        if guarded:
            return guarded
        if self.state.retired or not self.state.staged:
            return {"accepted": False, "reason": "INVALID_STATE_TRANSITION"}
        self._accept_transition(sequence, transition)
        self.state.activated = True
        self.save()
        return {"accepted": True, "reason": "SCOPE_ACTIVATED"}

    def select(self, *, current_available: bool, next_available: bool, next_valid: bool) -> dict[str, Any]:
        if not self.state.activated:
            return {"source": "current" if current_available else "unavailable", "reason": "CURRENT_AUTHORITATIVE_BEFORE_ACTIVATION"}
        if next_available and next_valid:
            return {"source": "next", "reason": "NEXT_AUTHORITATIVE_AFTER_ACTIVATION"}
        return {"source": "unavailable", "reason": "UNAVAILABLE_NEXT_NO_FALLBACK"}

    def retire(self, sequence: int) -> dict[str, Any]:
        transition = {"action": "retire", "sequence": sequence}
        guarded = self._guard(sequence, transition)
        if guarded:
            return guarded
        if not self.state.activated:
            return {"accepted": False, "reason": "INVALID_STATE_TRANSITION"}
        self._accept_transition(sequence, transition)
        self.state.retired = True
        self.save()
        return {"accepted": True, "reason": "CURRENT_RETIRED"}

    def snapshot(self) -> dict[str, Any]:
        return asdict(self.state)
