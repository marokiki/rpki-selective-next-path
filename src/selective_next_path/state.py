from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


WARNING = "EXPERIMENTAL / NOT FOR PRODUCTION"
SCHEMA_VERSION = 1


class CurrentSuiteState(StrEnum):
    SECURE = "secure"
    COMPROMISED = "compromised"
    RETIRED = "retired"


class NextTrustAnchorState(StrEnum):
    ABSENT = "absent"
    OBSERVED = "observed"
    ACCEPTED = "accepted"


class CARole(StrEnum):
    TRUST_ANCHOR = "trust_anchor"
    RIR_NIR = "rir_nir"
    HOSTED = "hosted"
    DELEGATED = "delegated"


class ManagementMode(StrEnum):
    HOSTED = "hosted"
    DELEGATED = "delegated"


class NextPreparation(StrEnum):
    PREBUILT = "prebuilt"
    ON_DEMAND = "on_demand"
    NONE = "none"


class CAState(StrEnum):
    CURRENT_ONLY = "current_only"
    NEXT_PARENT_AVAILABLE = "next_parent_available"
    NEXT_CA_STAGED = "next_ca_staged"
    DUAL_PUBLISHED = "dual_published"
    ACTIVATED = "activated"
    CURRENT_RETIRED = "current_retired"


STATE_RANK = {
    CAState.CURRENT_ONLY: 0,
    CAState.NEXT_PARENT_AVAILABLE: 1,
    CAState.NEXT_CA_STAGED: 2,
    CAState.DUAL_PUBLISHED: 3,
    CAState.ACTIVATED: 4,
    CAState.CURRENT_RETIRED: 5,
}


class Action(StrEnum):
    OBSERVE_NEXT_TA = "observe_next_ta"
    ACCEPT_NEXT_TA = "accept_next_ta"
    PREBUILD_NEXT_CA = "prebuild_next_ca"
    COMPROMISE_CURRENT = "compromise_current"
    CREATE_NEXT_CA = "create_next_ca"
    STAGE_NEXT_CA = "stage_next_ca"
    DUAL_PUBLISH = "dual_publish"
    ACTIVATE = "activate"
    RETIRE_CURRENT = "retire_current"
    FETCH_NEXT = "fetch_next"
    APPLY_SNAPSHOT = "apply_snapshot"


class ReasonCode(StrEnum):
    NEXT_TA_OBSERVED = "NEXT_TA_OBSERVED"
    NEXT_TA_ACCEPTED = "NEXT_TA_ACCEPTED"
    NEXT_CA_PREBUILT = "NEXT_CA_PREBUILT"
    CURRENT_SUITE_COMPROMISED = "CURRENT_SUITE_COMPROMISED"
    NEXT_CA_CREATED = "NEXT_CA_CREATED"
    NEXT_CA_STAGED = "NEXT_CA_STAGED"
    DUAL_PUBLICATION_STARTED = "DUAL_PUBLICATION_STARTED"
    SCOPE_ACTIVATED = "SCOPE_ACTIVATED"
    CURRENT_RETIRED = "CURRENT_RETIRED"
    NEXT_AVAILABLE = "NEXT_AVAILABLE"
    CURRENT_REMAINS_AUTHORITATIVE = "CURRENT_REMAINS_AUTHORITATIVE"
    IDEMPOTENT_TRANSITION = "IDEMPOTENT_TRANSITION"
    SNAPSHOT_APPLIED = "SNAPSHOT_APPLIED"

    CURRENT_SUITE_NOT_SECURE = "CURRENT_SUITE_NOT_SECURE"
    NEXT_TA_NOT_OBSERVED = "NEXT_TA_NOT_OBSERVED"
    NEXT_TA_REPLACEMENT_FORBIDDEN = "NEXT_TA_REPLACEMENT_FORBIDDEN"
    INVALID_NEXT_PARENT_PATH = "INVALID_NEXT_PARENT_PATH"
    CURRENT_SIGNATURE_INSUFFICIENT_AFTER_COMPROMISE = (
        "CURRENT_SIGNATURE_INSUFFICIENT_AFTER_COMPROMISE"
    )
    AUTHORITATIVE_HOSTED_OPERATOR_MISMATCH = (
        "AUTHORITATIVE_HOSTED_OPERATOR_MISMATCH"
    )
    AUTHORITATIVE_PARENT_MISMATCH = "AUTHORITATIVE_PARENT_MISMATCH"
    AUTHORITATIVE_REGISTRY_RECORD_MISSING = "AUTHORITATIVE_REGISTRY_RECORD_MISSING"
    AUTHORITATIVE_REGISTRY_RECORD_MISMATCH = (
        "AUTHORITATIVE_REGISTRY_RECORD_MISMATCH"
    )
    UNPREPARED_DELEGATED_CA = "UNPREPARED_DELEGATED_CA"
    NEXT_CA_NOT_STAGED = "NEXT_CA_NOT_STAGED"
    NEXT_OBJECTS_INVALID = "NEXT_OBJECTS_INVALID"
    RESOURCE_SEMANTICS_MISMATCH = "RESOURCE_SEMANTICS_MISMATCH"
    VRP_SEMANTICS_MISMATCH = "VRP_SEMANTICS_MISMATCH"
    ASPA_SEMANTICS_MISMATCH = "ASPA_SEMANTICS_MISMATCH"
    CHILD_DELEGATION_SEMANTICS_MISMATCH = (
        "CHILD_DELEGATION_SEMANTICS_MISMATCH"
    )
    SEQUENCE_REPLAY = "SEQUENCE_REPLAY"
    SEQUENCE_CONFLICT = "SEQUENCE_CONFLICT"
    STATE_ROLLBACK = "STATE_ROLLBACK"
    CURRENT_REINTRODUCTION_AFTER_RETIREMENT = (
        "CURRENT_REINTRODUCTION_AFTER_RETIREMENT"
    )
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
    UNAVAILABLE_NEXT_NO_FALLBACK = "UNAVAILABLE_NEXT_NO_FALLBACK"


@dataclass(frozen=True)
class ComparisonScope:
    resources: bool = True
    vrps: bool = True
    aspas: bool = False
    child_delegations: bool = False

    @classmethod
    def from_dict(cls, value: dict[str, Any] | None) -> ComparisonScope:
        return cls(**(value or {}))


@dataclass(frozen=True)
class SemanticPayload:
    resources: dict[str, Any] | None = None
    vrps: list[dict[str, Any]] | None = None
    aspas: list[dict[str, Any]] | None = None
    child_delegations: list[dict[str, Any]] | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any] | None) -> SemanticPayload:
        return cls(**(value or {}))


@dataclass(frozen=True)
class CA:
    ca_id: str
    operator_id: str
    role: CARole
    management_mode: ManagementMode
    parent_ca_id: str | None
    authoritative_parent_ca_id: str | None
    authoritative_registry_id: str | None
    next_preparation: NextPreparation
    resource_weight: int
    current_semantics: SemanticPayload
    comparison_scope: ComparisonScope


@dataclass(frozen=True)
class RegistryRecord:
    registry_id: str
    child_ca_id: str
    parent_ca_id: str
    operator_id: str
    resources: dict[str, Any]


@dataclass
class ScopeTransitionState:
    scope_id: str
    accepted_next_ta_id: str | None = None
    highest_transition_sequence: int = 0
    state: CAState = CAState.CURRENT_ONLY
    activated: bool = False
    retired: bool = False
    last_resource_digest: str | None = None
    last_vrp_digest: str | None = None
    last_aspa_digest: str | None = None
    last_child_delegation_digest: str | None = None
    last_transition_digest: str | None = None
    next_semantics: SemanticPayload = field(default_factory=SemanticPayload)
    next_objects_valid: bool = False


@dataclass(frozen=True)
class EventResult:
    schema_version: int
    global_step: int
    simulation_time: str
    scope_id: str
    transition_sequence: int | None
    previous_state: str
    requested_action: str
    resulting_state: str
    accepted: bool
    reason_code: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "global_step": self.global_step,
            "simulation_time": self.simulation_time,
            "scope_id": self.scope_id,
            "transition_sequence": self.transition_sequence,
            "previous_state": self.previous_state,
            "requested_action": self.requested_action,
            "resulting_state": self.resulting_state,
            "accepted": self.accepted,
            "reason_code": self.reason_code,
        }
