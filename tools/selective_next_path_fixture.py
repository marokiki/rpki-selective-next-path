#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from selective_next_path.cost import build_cost_model
from selective_next_path.model import TransitionModel
from selective_next_path.result_io import markdown_table, write_json
from selective_next_path.state import SCHEMA_VERSION, SemanticPayload, WARNING

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "testdata" / "selective-next-path" / "scenario.json"
RESULTS = ROOT / "results" / "selective-next-path"


def load_fixture(path: Path = FIXTURE) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def execute_event(
    model: TransitionModel,
    event: dict[str, Any],
):
    action = event["action"]
    if action == "observe_next_ta":
        return model.observe_next_ta(event["ta_id"])
    if action == "accept_next_ta":
        return model.accept_next_ta(event["ta_id"])
    if action == "prebuild_next_ca":
        ca = model.cas[event["ca_id"]]
        return model.prebuild_next_ca(
            event["ca_id"],
            event["sequence"],
            ca.current_semantics,
        )
    if action == "compromise_current":
        return model.compromise_current()
    if action == "create_next_ca":
        return model.create_next_ca(
            event["ca_id"],
            event["sequence"],
            current_signature_only=event.get(
                "current_signature_only",
                False,
            ),
        )
    if action == "stage_next_ca":
        semantics = (
            model.cas[event["ca_id"]].current_semantics
            if event.get("semantics_from_current")
            else SemanticPayload.from_dict(event["next_semantics"])
        )
        return model.stage_next_ca(
            event["ca_id"],
            event["sequence"],
            semantics,
            objects_valid=event.get("objects_valid", True),
        )
    if action == "dual_publish":
        return model.dual_publish(event["ca_id"], event["sequence"])
    if action == "activate":
        return model.activate(event["ca_id"], event["sequence"])
    if action == "retire_current":
        return model.retire_current(event["ca_id"], event["sequence"])
    if action == "fetch_next":
        return model.fetch_next(
            event["ca_id"],
            available=event["available"],
        )
    raise ValueError(f"unsupported fixture action: {action}")


def run_scenario(
    fixture: dict[str, Any],
) -> tuple[TransitionModel, dict[str, Any], dict[str, Any]]:
    model = TransitionModel.from_fixture(fixture)
    results = [execute_event(model, event) for event in fixture["events"]]
    reason_counts = Counter(result.reason_code for result in results)
    accepted = sum(result.accepted for result in results)
    assertions = {
        "next_ta_preaccepted": (
            model.accepted_next_ta_id == "next-ta-2035"
        ),
        "hosted_a_activated": model.scopes["hosted-a"].activated,
        "hosted_a_no_fallback": any(
            event.scope_id == "hosted-a"
            and event.reason_code == "UNAVAILABLE_NEXT_NO_FALLBACK"
            for event in results
        ),
        "new_ta_after_compromise_rejected": (
            reason_counts["CURRENT_SUITE_NOT_SECURE"] == 1
        ),
        "current_signed_key_rejected": (
            reason_counts[
                "CURRENT_SIGNATURE_INSUFFICIENT_AFTER_COMPROMISE"
            ]
            == 1
        ),
        "unprepared_delegated_rejected": (
            reason_counts["UNPREPARED_DELEGATED_CA"] == 1
        ),
        "prebuilt_delegated_activated": (
            model.scopes["delegated-prebuilt"].activated
        ),
        "sibling_remains_current": (
            model.scopes["hosted-sibling"].state.value == "current_only"
        ),
    }
    scenario = {
        "schema_version": SCHEMA_VERSION,
        "warning": WARNING,
        "scenario_id": "selective-next-path-phase-1",
        "simulation_epoch": fixture["simulation_epoch"],
        "input_events": fixture["events"],
        "event_log": [result.to_dict() for result in results],
        "accepted_action_count": accepted,
        "rejected_action_count": len(results) - accepted,
        "reason_code_counts": dict(sorted(reason_counts.items())),
        "assertions": assertions,
        "all_assertions_passed": all(assertions.values()),
        "semantic_comparisons": dict(sorted(model.comparison_log.items())),
        "final_state": model.export_state(),
    }
    migrating = {
        ca_id
        for ca_id, state in model.scopes.items()
        if state.activated and not state.retired
    }
    cost = build_cost_model(list(model.cas.values()), migrating)
    return model, scenario, cost


def render_report(
    model: TransitionModel,
    scenario: dict[str, Any],
    cost: dict[str, Any],
) -> str:
    state_rows = [
        {
            "ca_id": ca_id,
            "state": model.scopes[ca_id].state.value,
            "activated": str(model.scopes[ca_id].activated).lower(),
            "retired": str(model.scopes[ca_id].retired).lower(),
        }
        for ca_id in sorted(model.cas)
    ]
    security_failures = [
        {
            "step": event["global_step"],
            "scope_id": event["scope_id"],
            "action": event["requested_action"],
            "reason": event["reason_code"],
        }
        for event in scenario["event_log"]
        if not event["accepted"]
    ]
    cost_rows = [
        {
            "strategy": row["strategy"],
            "N": row["N"],
            "B": row["B"],
            "M": row["M"],
            "coverage": row[
                "post_compromise_migration_coverage"
            ]["ca_count_fraction"],
            "resource_coverage": row[
                "post_compromise_migration_coverage"
            ]["resource_weight_fraction"],
        }
        for row in cost["strategies"]
    ]
    return (
        "# Selective Next-path Phase 1 Report\n\n"
        "> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        "## Assumptions\n\n"
        "- Protocol-neutral deterministic state-machine model only.\n"
        "- No certificates, cryptography, RRDP, rsync, or validator behavior.\n"
        "- The Current Suite is forgeable after the modeled compromise event; "
        "the pre-accepted Next TA remains secure.\n\n"
        "## Scenario summary\n\n"
        f"- Accepted actions: {scenario['accepted_action_count']}\n"
        f"- Rejected actions: {scenario['rejected_action_count']}\n"
        f"- All assertions passed: `{str(scenario['all_assertions_passed']).lower()}`\n\n"
        + markdown_table(
            state_rows,
            [
                ("ca_id", "CA"),
                ("state", "State"),
                ("activated", "Activated"),
                ("retired", "Retired"),
            ],
        )
        + "\n\n## Cost comparison\n\n"
        + markdown_table(
            cost_rows,
            [
                ("strategy", "Strategy"),
                ("N", "N"),
                ("B", "B"),
                ("M", "M"),
                ("coverage", "CA coverage"),
                ("resource_coverage", "Resource coverage"),
            ],
        )
        + "\n\n## Security failures\n\n"
        + markdown_table(
            security_failures,
            [
                ("step", "Step"),
                ("scope_id", "Scope"),
                ("action", "Action"),
                ("reason", "Reason"),
            ],
        )
        + "\n\n## Unsupported features\n\n"
        "- Production RPKI validation or policy\n"
        "- Real certificates, CMS, PQ signatures, Krill, Routinator, or rpki-client\n"
        "- Secure out-of-band enrollment for an unprepared Delegated CA\n"
        "- Byte-size, RRDP, rsync, HSM, repository, or timing measurements\n"
        "- CCR as a protocol dependency\n\n"
        "## Reproduction\n\n"
        "```sh\n"
        "make selective-next-path\n"
        "make selective-next-path-test\n"
        "```\n"
    )


def generate(
    fixture_path: Path = FIXTURE,
    results_path: Path = RESULTS,
) -> None:
    fixture = load_fixture(fixture_path)
    model, scenario, cost = run_scenario(fixture)
    write_json(results_path / "topology.json", model.topology_document())
    write_json(results_path / "scenario-results.json", scenario)
    write_json(results_path / "cost-model.json", cost)
    (results_path / "report.md").parent.mkdir(parents=True, exist_ok=True)
    (results_path / "report.md").write_text(
        render_report(model, scenario, cost),
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    generate()


if __name__ == "__main__":
    main()
