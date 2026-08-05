#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import shutil
from pathlib import Path
from typing import Any

from selective_next_path.result_io import markdown_table, write_json
from selective_next_path.state import SCHEMA_VERSION, WARNING

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "testdata" / "selective-next-path" / "phase7-scale.json"
RESULTS = ROOT / "results" / "selective-next-path"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def strategy_row(n: int, name: str, config: dict[str, Any], sizes: dict[str, int], per_ca_generation_ns: int, per_scope_validation_ns: int) -> dict[str, Any]:
    m = max(1, math.ceil(n * config["concurrent_migration_fraction"]))
    if name == "all_cas_prebuilt":
        b, on_demand, covered, resource_coverage = n, 0, n, 1.0
    elif name == "selective_upper_path":
        b = max(1, math.ceil(n * config["selective_prebuilt_fraction"]))
        on_demand = min(m, math.ceil((n - b) * config["selective_hosted_fraction_of_remaining"]))
        covered = min(n, b + math.ceil((n - b) * config["selective_hosted_fraction_of_remaining"]))
        resource_coverage = config["selective_resource_coverage"]
    else:
        b, on_demand, covered, resource_coverage = 0, 0, 0, 0.0
    published_cas = b + on_demand
    object_count = published_cas * 3 + (m if covered else 0)
    publication_bytes = published_cas * (sizes["ca"] + sizes["crl"] + sizes["manifest"]) + (m if covered else 0) * sizes["roa"]
    return {
        "strategy": name,
        "N": n,
        "B": b,
        "M": m,
        "on_demand_generated": on_demand,
        "covered_ca_count": covered,
        "ca_coverage_fraction": round(covered / n, 6),
        "resource_coverage_fraction": resource_coverage,
        "publication_object_count": object_count,
        "publication_bytes": publication_bytes,
        "projected_generation_ns": published_cas * per_ca_generation_ns,
        "projected_validation_ns": covered * per_scope_validation_ns,
        "recovery": {"activated_scope_next_outage_unavailable": covered, "current_fallback_count": 0, "uncovered_scopes_remain_current": n - covered},
        "classification": "synthetic linear projection calibrated by Phase 3 single-run measurements",
    }


def generate(results_path: Path = RESULTS) -> dict[str, Any]:
    config = load_json(FIXTURE)
    phase3 = load_json(RESULTS / "phase3-real-fixture.json")
    phase4 = load_json(RESULTS / "phase4-pqc-fixture.json")
    next_suite = next(row for row in phase3["suites"] if row["suite"] == "next")
    sizes = {"ca": next_suite["artifacts_bytes"]["hosted_ca_certificate"], "crl": next_suite["artifacts_bytes"]["crl"], "manifest": next_suite["artifacts_bytes"]["manifest_cms"], "roa": next_suite["artifacts_bytes"]["roa_cms"]}
    timings = next_suite["timings_ns"]
    per_ca_generation = timings["crl_generation"] + timings["roa_issue_and_sign"] + timings["manifest_issue_and_sign"]
    per_scope_validation = timings["path_validation"] + timings["roa_cms_validation"] + timings["manifest_cms_validation"]
    rows = [strategy_row(n, strategy, config, sizes, per_ca_generation, per_scope_validation) for n in config["batch_sizes"] for strategy in ("all_cas_prebuilt", "selective_upper_path", "mixed_tree_only")]
    krill_binary = os.environ.get("PQC_RPKI_KRILL_BIN") or shutil.which("krill")
    krill_batches = [{"N": n, "status": "not-run" if krill_binary else "skipped", "reason": "Krill executable unavailable" if not krill_binary else "Krill is available but requires an explicitly configured isolated repository"} for n in config["batch_sizes"]]
    result = {
        "schema_version": SCHEMA_VERSION,
        "warning": WARNING,
        "phase": 7,
        "status": "synthetic-confirmed-krill-skipped" if not krill_binary else "synthetic-confirmed-krill-not-run",
        "inputs": {"scale_fixture": "testdata/selective-next-path/phase7-scale.json", "phase3_measurement": "results/selective-next-path/phase3-real-fixture.json", "phase4_evidence": "results/selective-next-path/phase4-pqc-fixture.json"},
        "calibration": {"suite": next_suite["algorithm"], "artifact_sizes_bytes": sizes, "per_ca_generation_ns": per_ca_generation, "per_scope_validation_ns": per_scope_validation, "phase4_mldsa_status": phase4["next_suites"][0]["status"]},
        "synthetic_scale_results": rows,
        "krill_backed_batches": krill_batches,
        "checks": {
            "all_batch_sizes_present": sorted({row["N"] for row in rows}) == config["batch_sizes"],
            "all_strategies_present": {row["strategy"] for row in rows} == {"all_cas_prebuilt", "selective_upper_path", "mixed_tree_only"},
            "selective_prebuild_smaller_than_full": all(next(row for row in rows if row["N"] == n and row["strategy"] == "selective_upper_path")["B"] < n for n in config["batch_sizes"]),
            "no_current_fallback_after_activation": all(row["recovery"]["current_fallback_count"] == 0 for row in rows),
            "publication_bytes_monotonic": all(next(row for row in rows if row["N"] == right and row["strategy"] == "all_cas_prebuilt")["publication_bytes"] > next(row for row in rows if row["N"] == left and row["strategy"] == "all_cas_prebuilt")["publication_bytes"] for left, right in zip(config["batch_sizes"], config["batch_sizes"][1:])),
        },
        "limitations": [
            "Scale values are linear projections from one Phase 3 P-256 run; they are not batch cryptographic measurements.",
            "ML-DSA evidence is recorded in Phase 4 but is not used for timing projection because comparable validation timing is unavailable.",
            "Krill-backed batches were skipped because no isolated Krill executable/repository is configured.",
            "RRDP, rsync, caching, concurrency, HSM behavior, and validator memory are not modeled.",
        ],
    }
    result["all_synthetic_checks_passed"] = all(result["checks"].values())
    write_json(results_path / "phase7-scale-evaluation.json", result)
    report_rows = [{"N": row["N"], "strategy": row["strategy"], "B": row["B"], "M": row["M"], "bytes": row["publication_bytes"], "CA coverage": row["ca_coverage_fraction"], "fallbacks": row["recovery"]["current_fallback_count"]} for row in rows]
    report = "# Selective Next-path Phase 7 Scale Evaluation\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\nSchema version: `1`\n\n" + markdown_table(report_rows, [("N", "N"), ("strategy", "Strategy"), ("B", "B"), ("M", "M"), ("bytes", "Projected bytes"), ("CA coverage", "CA coverage"), ("fallbacks", "Current fallbacks")])
    report += "\n\nSynthetic checks passed: `" + str(result["all_synthetic_checks_passed"]).lower() + "`\n\nKrill-backed batches: **" + krill_batches[0]["status"] + "**\n\n## Limitations\n\n" + "\n".join(f"- {item}" for item in result["limitations"]) + "\n"
    (results_path / "report-phase7.md").write_text(report, encoding="utf-8", newline="\n")
    return result


if __name__ == "__main__":
    generate()
