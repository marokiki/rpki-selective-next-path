#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from selective_next_path.result_io import markdown_table, write_json
from selective_next_path.rp_policy import RPTransitionPolicy
from selective_next_path.state import ComparisonScope, SCHEMA_VERSION, SemanticPayload, WARNING

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "testdata" / "selective-next-path" / "phase6-rp-policy.json"
RESULTS = ROOT / "results" / "selective-next-path"
LOCAL = ROOT / "local" / "selective-next-path" / "phase6"


def generate(results_path: Path = RESULTS) -> dict[str, Any]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    current = SemanticPayload.from_dict(fixture["current"])
    candidate = SemanticPayload.from_dict(fixture["next"])
    scope = ComparisonScope.from_dict(fixture["comparison_scope"])
    LOCAL.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="run-", dir=LOCAL) as name:
        state_path = Path(name) / "rp-transition-state.json"
        policy = RPTransitionPolicy.create(state_path, fixture["scope_id"], fixture["accepted_next_ta_id"])
        before = policy.select(current_available=True, next_available=True, next_valid=True)
        stage = policy.stage(1, fixture["accepted_next_ta_id"], current, candidate, scope, True)
        activate = policy.activate(2)
        after = policy.select(current_available=True, next_available=True, next_valid=True)
        outage = policy.select(current_available=True, next_available=False, next_valid=False)
        restarted = RPTransitionPolicy.load(state_path)
        replay = restarted.stage(1, fixture["accepted_next_ta_id"], current, candidate, scope, True)
        retirement = restarted.retire(3)
        current_still_published = restarted.select(current_available=True, next_available=True, next_valid=True)
        final_state = restarted.snapshot()
    checks = {
        "current_authoritative_before_activation": before["source"] == "current",
        "semantic_stage_accepted": stage["accepted"],
        "activation_accepted": activate["accepted"],
        "next_authoritative_after_activation": after["source"] == "next",
        "next_failure_has_no_current_fallback": outage["source"] == "unavailable" and outage["reason"] == "UNAVAILABLE_NEXT_NO_FALLBACK",
        "older_sequence_rejected_after_restart": replay["reason"] == "SEQUENCE_REPLAY",
        "retirement_monotonic": retirement["accepted"] and final_state["retired"],
        "current_publication_not_authoritative": current_still_published["source"] == "next",
    }
    events = [{"event": name, **value} for name, value in [("select_before", before), ("stage", stage), ("activate", activate), ("select_after", after), ("next_outage", outage), ("restart_replay", replay), ("retire", retirement), ("current_remains_published", current_still_published)]]
    result = {"schema_version": SCHEMA_VERSION, "warning": WARNING, "phase": 6, "status": "confirmed" if all(checks.values()) else "failed", "scope_id": fixture["scope_id"], "events": events, "checks": checks, "all_checks_passed": all(checks.values()), "persisted_state_schema": final_state, "state_storage": "local/selective-next-path/phase6 temporary test state", "limitations": ["This is a reference policy layer around RP-like semantic outputs, not a production validator.", "Certificate and repository validation results are inputs to the policy rather than performed by it.", "Persistence uses a single JSON file and does not provide transactional multi-process locking."]}
    write_json(results_path / "phase6-rp-policy.json", result)
    rows = [{"event": row["event"], "source": row.get("source", ""), "accepted": row.get("accepted", ""), "reason": row["reason"]} for row in events]
    report = "# Selective Next-path Phase 6 RP Policy\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\nSchema version: `1`\n\n" + markdown_table(rows, [("event", "Event"), ("source", "Selected source"), ("accepted", "Accepted"), ("reason", "Reason")])
    report += "\n\nAll checks passed: `" + str(result["all_checks_passed"]).lower() + "`\n\n## Limitations\n\n" + "\n".join(f"- {item}" for item in result["limitations"]) + "\n"
    (results_path / "report-phase6.md").write_text(report, encoding="utf-8", newline="\n")
    return result


if __name__ == "__main__":
    generate()
