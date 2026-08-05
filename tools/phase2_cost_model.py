#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from selective_next_path.phase2 import build_phase2_cost_model
from selective_next_path.result_io import markdown_table, write_json
from selective_next_path.state import SCHEMA_VERSION, WARNING
from tools.selective_next_path_fixture import load_fixture, run_scenario

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "testdata" / "selective-next-path" / "cost-inputs.json"
RESULTS = ROOT / "results" / "selective-next-path"


def load_inputs(path: Path = INPUTS) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_manifest(inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "warning": WARNING,
        "experiment_id": "selective-next-path-phase-2",
        "simulation_epoch": inputs["simulation_epoch"],
        "inputs": ["testdata/selective-next-path/scenario.json", "testdata/selective-next-path/cost-inputs.json"],
        "commands": ["make selective-next-path-phase2", "make selective-next-path-phase2-test"],
        "source": inputs["source"],
        "determinism": {"current_time_used": False, "random_identifiers_used": False, "canonical_json": True, "stable_row_sort": "strategy"},
    }


def render_report(model: dict[str, Any]) -> str:
    rows = []
    for row in sorted(model["strategies"], key=lambda value: value["strategy"]):
        estimate = row["estimated_storage_and_transfer"]
        coverage = row["post_compromise_migration_coverage"]
        rows.append({"strategy": row["strategy"], "N": row["N"], "B": row["B"], "M": row["M"], "on-demand": row["on_demand_generated_ca_count"], "bytes": estimate["publication_bytes"], "snapshot": estimate["rrdp_snapshot_bytes"], "delta": estimate["first_transition_rrdp_delta_bytes"], "CA coverage": coverage["ca_count_fraction"], "resource coverage": coverage["resource_weight_fraction"]})
    return (
        "# Selective Next-path Phase 2 Cost Model\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\nSchema version: `1`\n\n"
        "The model combines deterministic Phase 1 topology counts with public RSA object-size measurements and explicit synthetic RRDP overhead assumptions. Byte values are estimates, not transfer measurements.\n\n"
        + markdown_table(rows, [("strategy", "Strategy"), ("N", "N"), ("B", "B"), ("M", "M"), ("on-demand", "On-demand CA"), ("bytes", "Published bytes"), ("snapshot", "RRDP snapshot bytes"), ("delta", "First delta bytes"), ("CA coverage", "CA coverage"), ("resource coverage", "Resource coverage")])
        + "\n\n## Classification and limitations\n\n" + "\n".join(f"- {item}" for item in model["limitations"]) + "\n"
    )


def generate(results_path: Path = RESULTS) -> None:
    machine, _, _ = run_scenario(load_fixture())
    migrating = {ca_id for ca_id, state in machine.scopes.items() if state.activated and not state.retired}
    inputs = load_inputs()
    model = build_phase2_cost_model(list(machine.cas.values()), migrating, inputs)
    write_json(results_path / "cost-model-phase2.json", model)
    write_json(results_path / "experiment-manifest-phase2.json", build_manifest(inputs))
    report_path = results_path / "report-phase2.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(model), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    generate()
