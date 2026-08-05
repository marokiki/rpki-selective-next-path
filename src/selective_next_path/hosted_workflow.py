from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .state import SCHEMA_VERSION, WARNING


@dataclass(frozen=True)
class HostedWorkflow:
    parent_ca_id: str
    child_ca_id: str
    operator_id: str
    vrp: dict[str, Any]

    def dry_run(self) -> dict[str, Any]:
        events = [
            {"step": 1, "event": "next_parent_ready", "parent": self.parent_ca_id, "suite": "next", "accepted": True},
            {"step": 2, "event": "assert_hosted_child_absent", "child": self.child_ca_id, "accepted": True},
            {"step": 3, "event": "mark_current_compromised", "classification": "controller policy event", "accepted": True},
            {"step": 4, "event": "create_hosted_child", "child": self.child_ca_id, "issuer": self.parent_ca_id, "suite": "next", "operator": self.operator_id, "accepted": True},
            {"step": 5, "event": "publish", "objects": ["CA certificate", "CRL", "Manifest", "ROA"], "accepted": True},
            {"step": 6, "event": "activate", "valid_next_path": True, "semantic_vrp_match": True, "accepted": True},
            {"step": 7, "event": "next_unavailable", "output": "unavailable", "current_fallback": False, "accepted": True},
        ]
        return {
            "schema_version": SCHEMA_VERSION,
            "warning": WARNING,
            "events": events,
            "checks": {
                "child_absent_before_transition": events[1]["event"] == "assert_hosted_child_absent",
                "created_after_compromise": events[3]["step"] > events[2]["step"],
                "issued_by_next_parent_only": events[3]["suite"] == "next" and events[3]["issuer"] == self.parent_ca_id,
                "required_objects_requested": set(events[4]["objects"]) == {"CA certificate", "CRL", "Manifest", "ROA"},
                "no_current_fallback": events[-1]["current_fallback"] is False,
            },
            "vrp": self.vrp,
        }
