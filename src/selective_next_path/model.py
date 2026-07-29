from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .semantics import (
    canonical_payload,
    compare_payloads,
    normalize_resources,
    payload_digests,
    semantic_digest,
)
from .state import (
    Action,
    CA,
    CARole,
    CAState,
    ComparisonScope,
    CurrentSuiteState,
    EventResult,
    ManagementMode,
    NextPreparation,
    NextTrustAnchorState,
    ReasonCode,
    RegistryRecord,
    SCHEMA_VERSION,
    STATE_RANK,
    ScopeTransitionState,
    SemanticPayload,
    WARNING,
)


class TransitionModel:
    """Protocol-neutral deterministic transition model."""

    def __init__(
        self,
        simulation_epoch: str,
        cas: list[CA],
        registry_records: list[RegistryRecord],
    ) -> None:
        self.simulation_epoch = simulation_epoch
        self.cas = {ca.ca_id: ca for ca in cas}
        self.registry_records = {
            record.registry_id: record for record in registry_records
        }
        self.current_suite_state = CurrentSuiteState.SECURE
        self.next_ta_state = NextTrustAnchorState.ABSENT
        self.observed_next_ta_id: str | None = None
        self.accepted_next_ta_id: str | None = None
        self.global_step = 0
        self.scopes = {
            ca_id: ScopeTransitionState(scope_id=ca_id)
            for ca_id in sorted(self.cas)
        }
        self.event_log: list[EventResult] = []
        self.comparison_log: dict[str, dict[str, Any]] = {}

    @classmethod
    def from_fixture(cls, fixture: dict[str, Any]) -> TransitionModel:
        default_scope = ComparisonScope.from_dict(fixture.get("comparison_scope"))
        cas = []
        for row in fixture["cas"]:
            cas.append(
                CA(
                    ca_id=row["ca_id"],
                    operator_id=row["operator_id"],
                    role=CARole(row["role"]),
                    management_mode=ManagementMode(row["management_mode"]),
                    parent_ca_id=row.get("parent_ca_id"),
                    authoritative_parent_ca_id=row.get(
                        "authoritative_parent_ca_id"
                    ),
                    authoritative_registry_id=row.get(
                        "authoritative_registry_id"
                    ),
                    next_preparation=NextPreparation(row["next_preparation"]),
                    resource_weight=int(row["resource_weight"]),
                    current_semantics=SemanticPayload.from_dict(
                        row.get("current_semantics")
                    ),
                    comparison_scope=ComparisonScope.from_dict(
                        row.get("comparison_scope")
                        or asdict(default_scope)
                    ),
                )
            )
        records = [
            RegistryRecord(
                registry_id=row["registry_id"],
                child_ca_id=row["child_ca_id"],
                parent_ca_id=row["parent_ca_id"],
                operator_id=row["operator_id"],
                resources=row["resources"],
            )
            for row in fixture.get("registry_records", [])
        ]
        return cls(fixture["simulation_epoch"], cas, records)

    def _record(
        self,
        *,
        scope_id: str,
        sequence: int | None,
        previous_state: str,
        action: Action,
        resulting_state: str,
        accepted: bool,
        reason: ReasonCode,
    ) -> EventResult:
        self.global_step += 1
        event = EventResult(
            schema_version=SCHEMA_VERSION,
            global_step=self.global_step,
            simulation_time=self.simulation_epoch,
            scope_id=scope_id,
            transition_sequence=sequence,
            previous_state=previous_state,
            requested_action=action.value,
            resulting_state=resulting_state,
            accepted=accepted,
            reason_code=reason.value,
        )
        self.event_log.append(event)
        return event

    def _global_event(
        self,
        action: Action,
        previous: str,
        resulting: str,
        accepted: bool,
        reason: ReasonCode,
    ) -> EventResult:
        return self._record(
            scope_id="global",
            sequence=None,
            previous_state=previous,
            action=action,
            resulting_state=resulting,
            accepted=accepted,
            reason=reason,
        )

    def observe_next_ta(self, ta_id: str) -> EventResult:
        previous = self.next_ta_state.value
        if (
            self.accepted_next_ta_id is not None
            and ta_id != self.accepted_next_ta_id
        ):
            return self._global_event(
                Action.OBSERVE_NEXT_TA,
                previous,
                previous,
                False,
                ReasonCode.NEXT_TA_REPLACEMENT_FORBIDDEN,
            )
        self.observed_next_ta_id = ta_id
        self.next_ta_state = NextTrustAnchorState.OBSERVED
        return self._global_event(
            Action.OBSERVE_NEXT_TA,
            previous,
            self.next_ta_state.value,
            True,
            ReasonCode.NEXT_TA_OBSERVED,
        )

    def accept_next_ta(self, ta_id: str) -> EventResult:
        previous = self.next_ta_state.value
        if self.current_suite_state is not CurrentSuiteState.SECURE:
            return self._global_event(
                Action.ACCEPT_NEXT_TA,
                previous,
                previous,
                False,
                ReasonCode.CURRENT_SUITE_NOT_SECURE,
            )
        if (
            self.accepted_next_ta_id is not None
            and ta_id != self.accepted_next_ta_id
        ):
            return self._global_event(
                Action.ACCEPT_NEXT_TA,
                previous,
                previous,
                False,
                ReasonCode.NEXT_TA_REPLACEMENT_FORBIDDEN,
            )
        if (
            self.next_ta_state is not NextTrustAnchorState.OBSERVED
            or self.observed_next_ta_id != ta_id
        ):
            return self._global_event(
                Action.ACCEPT_NEXT_TA,
                previous,
                previous,
                False,
                ReasonCode.NEXT_TA_NOT_OBSERVED,
            )
        self.accepted_next_ta_id = ta_id
        self.next_ta_state = NextTrustAnchorState.ACCEPTED
        return self._global_event(
            Action.ACCEPT_NEXT_TA,
            previous,
            self.next_ta_state.value,
            True,
            ReasonCode.NEXT_TA_ACCEPTED,
        )

    def compromise_current(self) -> EventResult:
        previous = self.current_suite_state.value
        if self.current_suite_state is not CurrentSuiteState.SECURE:
            return self._global_event(
                Action.COMPROMISE_CURRENT,
                previous,
                previous,
                False,
                ReasonCode.INVALID_STATE_TRANSITION,
            )
        self.current_suite_state = CurrentSuiteState.COMPROMISED
        return self._global_event(
            Action.COMPROMISE_CURRENT,
            previous,
            self.current_suite_state.value,
            True,
            ReasonCode.CURRENT_SUITE_COMPROMISED,
        )

    def _valid_next_path(self, ca: CA) -> bool:
        if self.accepted_next_ta_id is None:
            return False
        if ca.role is CARole.TRUST_ANCHOR:
            return ca.ca_id == self.accepted_next_ta_id
        if ca.parent_ca_id is None or ca.parent_ca_id not in self.scopes:
            return False
        parent = self.scopes[ca.parent_ca_id]
        return (
            parent.accepted_next_ta_id == self.accepted_next_ta_id
            and STATE_RANK[parent.state] >= STATE_RANK[CAState.NEXT_CA_STAGED]
        )

    @staticmethod
    def _transition_fingerprint(
        action: Action,
        target_state: CAState,
        accepted_next_ta_id: str | None,
        digests: dict[str, str | None],
        extra: dict[str, Any] | None = None,
    ) -> str:
        return semantic_digest(
            {
                "action": action.value,
                "target_state": target_state.value,
                "accepted_next_ta_id": accepted_next_ta_id,
                "digests": digests,
                "extra": extra or {},
            }
        ) or ""

    def _transition(
        self,
        *,
        ca_id: str,
        sequence: int,
        action: Action,
        target_state: CAState,
        success_reason: ReasonCode,
        next_semantics: SemanticPayload | None = None,
        objects_valid: bool | None = None,
        extra: dict[str, Any] | None = None,
    ) -> EventResult:
        scope = self.scopes[ca_id]
        previous = scope.state
        semantics = next_semantics or scope.next_semantics
        digests = payload_digests(semantics)
        fingerprint = self._transition_fingerprint(
            action,
            target_state,
            self.accepted_next_ta_id,
            digests,
            extra,
        )
        if sequence < scope.highest_transition_sequence:
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=previous.value,
                action=action,
                resulting_state=previous.value,
                accepted=False,
                reason=ReasonCode.SEQUENCE_REPLAY,
            )
        if sequence == scope.highest_transition_sequence:
            if fingerprint == scope.last_transition_digest:
                return self._record(
                    scope_id=ca_id,
                    sequence=sequence,
                    previous_state=previous.value,
                    action=action,
                    resulting_state=previous.value,
                    accepted=True,
                    reason=ReasonCode.IDEMPOTENT_TRANSITION,
                )
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=previous.value,
                action=action,
                resulting_state=previous.value,
                accepted=False,
                reason=ReasonCode.SEQUENCE_CONFLICT,
            )
        if (
            scope.accepted_next_ta_id is not None
            and self.accepted_next_ta_id != scope.accepted_next_ta_id
        ):
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=previous.value,
                action=action,
                resulting_state=previous.value,
                accepted=False,
                reason=ReasonCode.NEXT_TA_REPLACEMENT_FORBIDDEN,
            )
        if scope.activated and STATE_RANK[target_state] < STATE_RANK[CAState.ACTIVATED]:
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=previous.value,
                action=action,
                resulting_state=previous.value,
                accepted=False,
                reason=ReasonCode.STATE_ROLLBACK,
            )
        if scope.retired and target_state is not CAState.CURRENT_RETIRED:
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=previous.value,
                action=action,
                resulting_state=previous.value,
                accepted=False,
                reason=ReasonCode.CURRENT_REINTRODUCTION_AFTER_RETIREMENT,
            )
        scope.highest_transition_sequence = sequence
        scope.state = target_state
        scope.accepted_next_ta_id = self.accepted_next_ta_id
        scope.next_semantics = semantics
        scope.last_resource_digest = digests["resources"]
        scope.last_vrp_digest = digests["vrps"]
        scope.last_aspa_digest = digests["aspas"]
        scope.last_child_delegation_digest = digests["child_delegations"]
        scope.last_transition_digest = fingerprint
        if objects_valid is not None:
            scope.next_objects_valid = objects_valid
        if target_state is CAState.ACTIVATED:
            scope.activated = True
        if target_state is CAState.CURRENT_RETIRED:
            scope.activated = True
            scope.retired = True
        return self._record(
            scope_id=ca_id,
            sequence=sequence,
            previous_state=previous.value,
            action=action,
            resulting_state=target_state.value,
            accepted=True,
            reason=success_reason,
        )

    def prebuild_next_ca(
        self,
        ca_id: str,
        sequence: int,
        next_semantics: SemanticPayload | None = None,
    ) -> EventResult:
        ca = self.cas[ca_id]
        previous = self.scopes[ca_id].state.value
        if self.current_suite_state is not CurrentSuiteState.SECURE:
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=previous,
                action=Action.PREBUILD_NEXT_CA,
                resulting_state=previous,
                accepted=False,
                reason=ReasonCode.CURRENT_SUITE_NOT_SECURE,
            )
        if ca.next_preparation is not NextPreparation.PREBUILT:
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=previous,
                action=Action.PREBUILD_NEXT_CA,
                resulting_state=previous,
                accepted=False,
                reason=ReasonCode.INVALID_STATE_TRANSITION,
            )
        if not self._valid_next_path(ca):
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=previous,
                action=Action.PREBUILD_NEXT_CA,
                resulting_state=previous,
                accepted=False,
                reason=ReasonCode.INVALID_NEXT_PARENT_PATH,
            )
        return self._transition(
            ca_id=ca_id,
            sequence=sequence,
            action=Action.PREBUILD_NEXT_CA,
            target_state=CAState.NEXT_CA_STAGED,
            success_reason=ReasonCode.NEXT_CA_PREBUILT,
            next_semantics=next_semantics or ca.current_semantics,
            objects_valid=True,
        )

    def create_next_ca(
        self,
        ca_id: str,
        sequence: int,
        *,
        current_signature_only: bool = False,
    ) -> EventResult:
        ca = self.cas[ca_id]
        previous = self.scopes[ca_id].state.value
        if (
            current_signature_only
            and self.current_suite_state is not CurrentSuiteState.SECURE
        ):
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=previous,
                action=Action.CREATE_NEXT_CA,
                resulting_state=previous,
                accepted=False,
                reason=ReasonCode.CURRENT_SIGNATURE_INSUFFICIENT_AFTER_COMPROMISE,
            )
        if not self._valid_next_path(ca):
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=previous,
                action=Action.CREATE_NEXT_CA,
                resulting_state=previous,
                accepted=False,
                reason=ReasonCode.INVALID_NEXT_PARENT_PATH,
            )
        if ca.management_mode is ManagementMode.DELEGATED:
            if ca.next_preparation is not NextPreparation.PREBUILT:
                return self._record(
                    scope_id=ca_id,
                    sequence=sequence,
                    previous_state=previous,
                    action=Action.CREATE_NEXT_CA,
                    resulting_state=previous,
                    accepted=False,
                    reason=ReasonCode.UNPREPARED_DELEGATED_CA,
                )
        else:
            parent = self.cas.get(ca.parent_ca_id or "")
            if parent is None or parent.operator_id != ca.operator_id:
                return self._record(
                    scope_id=ca_id,
                    sequence=sequence,
                    previous_state=previous,
                    action=Action.CREATE_NEXT_CA,
                    resulting_state=previous,
                    accepted=False,
                    reason=ReasonCode.AUTHORITATIVE_HOSTED_OPERATOR_MISMATCH,
                )
            if ca.authoritative_parent_ca_id != parent.ca_id:
                return self._record(
                    scope_id=ca_id,
                    sequence=sequence,
                    previous_state=previous,
                    action=Action.CREATE_NEXT_CA,
                    resulting_state=previous,
                    accepted=False,
                    reason=ReasonCode.AUTHORITATIVE_PARENT_MISMATCH,
                )
            record = self.registry_records.get(
                ca.authoritative_registry_id or ""
            )
            if record is None:
                return self._record(
                    scope_id=ca_id,
                    sequence=sequence,
                    previous_state=previous,
                    action=Action.CREATE_NEXT_CA,
                    resulting_state=previous,
                    accepted=False,
                    reason=ReasonCode.AUTHORITATIVE_REGISTRY_RECORD_MISSING,
                )
            expected = (
                record.child_ca_id == ca.ca_id
                and record.parent_ca_id == parent.ca_id
                and record.operator_id == ca.operator_id
                and normalize_resources(record.resources)
                == normalize_resources(ca.current_semantics.resources or {})
            )
            if not expected:
                return self._record(
                    scope_id=ca_id,
                    sequence=sequence,
                    previous_state=previous,
                    action=Action.CREATE_NEXT_CA,
                    resulting_state=previous,
                    accepted=False,
                    reason=ReasonCode.AUTHORITATIVE_REGISTRY_RECORD_MISMATCH,
                )
        return self._transition(
            ca_id=ca_id,
            sequence=sequence,
            action=Action.CREATE_NEXT_CA,
            target_state=CAState.NEXT_PARENT_AVAILABLE,
            success_reason=ReasonCode.NEXT_CA_CREATED,
            next_semantics=SemanticPayload(),
            objects_valid=False,
        )

    def stage_next_ca(
        self,
        ca_id: str,
        sequence: int,
        next_semantics: SemanticPayload,
        *,
        objects_valid: bool = True,
    ) -> EventResult:
        scope = self.scopes[ca_id]
        if scope.state not in {
            CAState.NEXT_PARENT_AVAILABLE,
            CAState.NEXT_CA_STAGED,
        }:
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=scope.state.value,
                action=Action.STAGE_NEXT_CA,
                resulting_state=scope.state.value,
                accepted=False,
                reason=ReasonCode.INVALID_STATE_TRANSITION,
            )
        return self._transition(
            ca_id=ca_id,
            sequence=sequence,
            action=Action.STAGE_NEXT_CA,
            target_state=CAState.NEXT_CA_STAGED,
            success_reason=ReasonCode.NEXT_CA_STAGED,
            next_semantics=next_semantics,
            objects_valid=objects_valid,
        )

    def dual_publish(self, ca_id: str, sequence: int) -> EventResult:
        scope = self.scopes[ca_id]
        if scope.state is not CAState.NEXT_CA_STAGED:
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=scope.state.value,
                action=Action.DUAL_PUBLISH,
                resulting_state=scope.state.value,
                accepted=False,
                reason=ReasonCode.NEXT_CA_NOT_STAGED,
            )
        if not scope.next_objects_valid:
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=scope.state.value,
                action=Action.DUAL_PUBLISH,
                resulting_state=scope.state.value,
                accepted=False,
                reason=ReasonCode.NEXT_OBJECTS_INVALID,
            )
        return self._transition(
            ca_id=ca_id,
            sequence=sequence,
            action=Action.DUAL_PUBLISH,
            target_state=CAState.DUAL_PUBLISHED,
            success_reason=ReasonCode.DUAL_PUBLICATION_STARTED,
        )

    def activate(self, ca_id: str, sequence: int) -> EventResult:
        ca = self.cas[ca_id]
        scope = self.scopes[ca_id]
        if scope.state is not CAState.DUAL_PUBLISHED:
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=scope.state.value,
                action=Action.ACTIVATE,
                resulting_state=scope.state.value,
                accepted=False,
                reason=ReasonCode.NEXT_CA_NOT_STAGED,
            )
        if not self._valid_next_path(ca):
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=scope.state.value,
                action=Action.ACTIVATE,
                resulting_state=scope.state.value,
                accepted=False,
                reason=ReasonCode.INVALID_NEXT_PARENT_PATH,
            )
        if not scope.next_objects_valid:
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=scope.state.value,
                action=Action.ACTIVATE,
                resulting_state=scope.state.value,
                accepted=False,
                reason=ReasonCode.NEXT_OBJECTS_INVALID,
            )
        equivalent, reason, details = compare_payloads(
            ca.current_semantics,
            scope.next_semantics,
            ca.comparison_scope,
        )
        self.comparison_log[ca_id] = details
        if not equivalent:
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=scope.state.value,
                action=Action.ACTIVATE,
                resulting_state=scope.state.value,
                accepted=False,
                reason=reason or ReasonCode.INVALID_STATE_TRANSITION,
            )
        return self._transition(
            ca_id=ca_id,
            sequence=sequence,
            action=Action.ACTIVATE,
            target_state=CAState.ACTIVATED,
            success_reason=ReasonCode.SCOPE_ACTIVATED,
        )

    def fetch_next(self, ca_id: str, *, available: bool) -> EventResult:
        scope = self.scopes[ca_id]
        if available:
            reason = ReasonCode.NEXT_AVAILABLE
            accepted = True
        elif scope.activated:
            reason = ReasonCode.UNAVAILABLE_NEXT_NO_FALLBACK
            accepted = False
        else:
            reason = ReasonCode.CURRENT_REMAINS_AUTHORITATIVE
            accepted = True
        return self._record(
            scope_id=ca_id,
            sequence=None,
            previous_state=scope.state.value,
            action=Action.FETCH_NEXT,
            resulting_state=scope.state.value,
            accepted=accepted,
            reason=reason,
        )

    def retire_current(self, ca_id: str, sequence: int) -> EventResult:
        scope = self.scopes[ca_id]
        if scope.state is not CAState.ACTIVATED:
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=scope.state.value,
                action=Action.RETIRE_CURRENT,
                resulting_state=scope.state.value,
                accepted=False,
                reason=ReasonCode.INVALID_STATE_TRANSITION,
            )
        return self._transition(
            ca_id=ca_id,
            sequence=sequence,
            action=Action.RETIRE_CURRENT,
            target_state=CAState.CURRENT_RETIRED,
            success_reason=ReasonCode.CURRENT_RETIRED,
        )

    def apply_snapshot(
        self,
        ca_id: str,
        *,
        sequence: int,
        state: CAState,
        accepted_next_ta_id: str | None,
        next_semantics: SemanticPayload,
        activated: bool,
        retired: bool,
    ) -> EventResult:
        scope = self.scopes[ca_id]
        if (
            scope.accepted_next_ta_id is not None
            and accepted_next_ta_id != scope.accepted_next_ta_id
        ):
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=scope.state.value,
                action=Action.APPLY_SNAPSHOT,
                resulting_state=scope.state.value,
                accepted=False,
                reason=ReasonCode.NEXT_TA_REPLACEMENT_FORBIDDEN,
            )
        if scope.activated and not activated:
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=scope.state.value,
                action=Action.APPLY_SNAPSHOT,
                resulting_state=scope.state.value,
                accepted=False,
                reason=ReasonCode.STATE_ROLLBACK,
            )
        if scope.retired and not retired:
            return self._record(
                scope_id=ca_id,
                sequence=sequence,
                previous_state=scope.state.value,
                action=Action.APPLY_SNAPSHOT,
                resulting_state=scope.state.value,
                accepted=False,
                reason=ReasonCode.CURRENT_REINTRODUCTION_AFTER_RETIREMENT,
            )
        return self._transition(
            ca_id=ca_id,
            sequence=sequence,
            action=Action.APPLY_SNAPSHOT,
            target_state=state,
            success_reason=ReasonCode.SNAPSHOT_APPLIED,
            next_semantics=next_semantics,
            objects_valid=True,
            extra={"activated": activated, "retired": retired},
        )

    def export_state(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "warning": WARNING,
            "simulation_epoch": self.simulation_epoch,
            "global_step": self.global_step,
            "current_suite_state": self.current_suite_state.value,
            "next_trust_anchor_state": self.next_ta_state.value,
            "observed_next_ta_id": self.observed_next_ta_id,
            "accepted_next_ta_id": self.accepted_next_ta_id,
            "scopes": [
                {
                    "scope_id": scope.scope_id,
                    "accepted_next_ta_id": scope.accepted_next_ta_id,
                    "highest_transition_sequence": (
                        scope.highest_transition_sequence
                    ),
                    "state": scope.state.value,
                    "activated": scope.activated,
                    "retired": scope.retired,
                    "last_resource_digest": scope.last_resource_digest,
                    "last_vrp_digest": scope.last_vrp_digest,
                    "last_aspa_digest": scope.last_aspa_digest,
                    "last_child_delegation_digest": (
                        scope.last_child_delegation_digest
                    ),
                    "last_transition_digest": scope.last_transition_digest,
                    "next_semantics": canonical_payload(scope.next_semantics),
                    "next_objects_valid": scope.next_objects_valid,
                }
                for scope in sorted(
                    self.scopes.values(),
                    key=lambda item: item.scope_id,
                )
            ],
        }

    @classmethod
    def restore(
        cls,
        fixture: dict[str, Any],
        saved: dict[str, Any],
    ) -> TransitionModel:
        model = cls.from_fixture(fixture)
        model.global_step = int(saved["global_step"])
        model.current_suite_state = CurrentSuiteState(
            saved["current_suite_state"]
        )
        model.next_ta_state = NextTrustAnchorState(
            saved["next_trust_anchor_state"]
        )
        model.observed_next_ta_id = saved.get("observed_next_ta_id")
        model.accepted_next_ta_id = saved.get("accepted_next_ta_id")
        for row in saved["scopes"]:
            scope = model.scopes[row["scope_id"]]
            scope.accepted_next_ta_id = row.get("accepted_next_ta_id")
            scope.highest_transition_sequence = int(
                row["highest_transition_sequence"]
            )
            scope.state = CAState(row["state"])
            scope.activated = bool(row["activated"])
            scope.retired = bool(row["retired"])
            scope.last_resource_digest = row.get("last_resource_digest")
            scope.last_vrp_digest = row.get("last_vrp_digest")
            scope.last_aspa_digest = row.get("last_aspa_digest")
            scope.last_child_delegation_digest = row.get(
                "last_child_delegation_digest"
            )
            scope.last_transition_digest = row.get("last_transition_digest")
            scope.next_semantics = SemanticPayload.from_dict(
                row.get("next_semantics")
            )
            scope.next_objects_valid = bool(row["next_objects_valid"])
        return model

    def topology_document(self) -> dict[str, Any]:
        cas = []
        relationships = []
        for ca_id in sorted(self.cas):
            ca = self.cas[ca_id]
            scope = self.scopes[ca_id]
            cas.append(
                {
                    "ca_id": ca.ca_id,
                    "operator_id": ca.operator_id,
                    "role": ca.role.value,
                    "management_mode": ca.management_mode.value,
                    "parent_ca_id": ca.parent_ca_id,
                    "authoritative_parent_ca_id": (
                        ca.authoritative_parent_ca_id
                    ),
                    "authoritative_registry_id": (
                        ca.authoritative_registry_id
                    ),
                    "resource_weight": ca.resource_weight,
                    "current_state": (
                        "retired" if scope.retired else "published"
                    ),
                    "next_state": scope.state.value,
                    "next_preparation": ca.next_preparation.value,
                    "current_resources": canonical_payload(
                        ca.current_semantics
                    )["resources"],
                    "next_resources": canonical_payload(
                        scope.next_semantics
                    )["resources"],
                }
            )
            if ca.parent_ca_id is not None:
                relationships.append(
                    {
                        "child_ca_id": ca.ca_id,
                        "parent_ca_id": ca.parent_ca_id,
                    }
                )
        return {
            "schema_version": SCHEMA_VERSION,
            "warning": WARNING,
            "simulation_epoch": self.simulation_epoch,
            "current_suite_state": self.current_suite_state.value,
            "next_trust_anchor_state": self.next_ta_state.value,
            "accepted_next_ta_id": self.accepted_next_ta_id,
            "cas": cas,
            "relationships": sorted(
                relationships,
                key=lambda row: (row["parent_ca_id"], row["child_ca_id"]),
            ),
        }
