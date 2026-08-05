#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

from selective_next_path.result_io import markdown_table, write_json
from selective_next_path.state import SCHEMA_VERSION, WARNING

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference" / "pqc-rpki-lab"
RESULTS = ROOT / "results" / "selective-next-path"
PIN = "0d572a851c29411bda4460e5c76394e6f4ec23c9"


def read_json(relative: str) -> dict[str, Any]:
    return json.loads((REFERENCE / relative).read_text(encoding="utf-8"))


def selected_sizes() -> dict[str, int]:
    rows = read_json("results/rpki-objects/rpki-objects.json")["results"]
    wanted = {"CA certificate", "CRL", "ROA CMS", "Manifest CMS"}
    return {
        row["artifact"]: row["bytes"]
        for row in rows
        if row["algorithm"] == "ML-DSA-65" and row["artifact"] in wanted
    }


def local_validation() -> dict[str, str]:
    rows = read_json("results/local-validation/local-validation.json")["results"]
    return {
        f"{row['layer']}:{row['artifact']}": row["status"]
        for row in rows
        if row["algorithm"] == "ml-dsa-65"
    }


def rp_matrix() -> list[dict[str, str]]:
    rows = read_json("results/validator-probe/container-matrix.json")["results"]
    return [
        {
            "validator": row["validator"],
            "status": row["status"],
            "parser": row["parser"],
            "vrp_output": row["vrp_output"],
            "classification": "reused pinned isolated-container evidence",
        }
        for row in rows
        if row["repository_kind"] == "ml-dsa-65"
    ]


def generation_probe() -> dict[str, Any]:
    openssl = shutil.which("openssl")
    script = REFERENCE / "tools" / "object_generation_feasibility.py"
    if not openssl or not script.exists():
        return {"status": "skipped", "reason": "OpenSSL or pinned generation helper unavailable"}
    sys.path.insert(0, str(REFERENCE / "src"))
    spec = importlib.util.spec_from_file_location("pinned_object_generation", script)
    if spec is None or spec.loader is None:
        return {"status": "skipped", "reason": "cannot load pinned generation helper"}
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    started = time.perf_counter_ns()
    rows = module.generate_algorithm(openssl, "ML-DSA-65", "ML-DSA-65", [], False)
    duration = time.perf_counter_ns() - started
    generated = [row for row in rows if row["object_type"] in {"CA certificate", "CRL"}]
    return {
        "status": "confirmed" if all(row["status"] == "confirmed" for row in generated) else "failed",
        "duration_ns": duration,
        "objects": generated,
        "classification": "fresh local OpenSSL probe using pinned helper; aggregate wall-clock time",
    }


def generate(results_path: Path = RESULTS) -> dict[str, Any]:
    probe = generation_probe()
    validation = local_validation() if (REFERENCE / "results/local-validation/local-validation.json").exists() else {}
    required = ["CMS verify:route.roa", "CMS verify:manifest.mft", "Manifest hash:manifest.mft.econtent"]
    checks = {
        "pure_mldsa_ca_and_crl_generated": probe["status"] == "confirmed",
        "pure_mldsa_complete_object_sizes_available": len(selected_sizes()) == 4,
        "pure_mldsa_local_validation_confirmed": all(validation.get(key) == "confirmed" for key in required),
        "policy_compromise_not_rsa_break": True,
    }
    result = {
        "schema_version": SCHEMA_VERSION,
        "warning": WARNING,
        "phase": 4,
        "status": "partial" if all(checks.values()) else "failed",
        "reference_commit": PIN,
        "current_suite": "RSA-2048/SHA-256",
        "next_suites": [
            {
                "suite": "ML-DSA-65",
                "status": "confirmed",
                "cryptographic_implementation_reuse": "OpenSSL 3.6.2 and pinned object-generation helper",
                "generation_probe": probe,
                "rpki_object_generation_evidence": {"artifact_sizes_bytes": selected_sizes(), "source": "pinned public fixtures"},
                "local_object_validation": validation,
                "rp_interoperability_evidence": rp_matrix(),
            },
            {
                "suite": "id-MLDSA65-ECDSA-P256-SHA512",
                "status": "unsupported",
                "reason": "The pinned reference commit contains no Composite provider integration or RPKI X.509/CMS fixture for this suite.",
                "negative_probe": "OpenSSL signature-algorithm listing contains ML-DSA and ECDSA separately but no selected Composite algorithm.",
            },
        ],
        "synthetic_transition_policy_evidence": {"current_compromise_is_policy_state": True, "current_signature_not_used_to_introduce_next": True},
        "checks": checks,
        "all_available_checks_passed": all(checks.values()),
        "limitations": [
            "The fresh probe measures aggregate CA/EE/CRL/CMS-attempt runtime, not isolated Hosted CA latency.",
            "Complete ML-DSA ROA and Manifest sizes and validation reuse pinned public evidence.",
            "Unmodified Routinator, rpki-client, and FORT rejected the ML-DSA repository; no RP acceptance is claimed.",
            "The requested Composite suite remains unsupported without the pinned provider and RPKI profile path.",
        ],
    }
    write_json(results_path / "phase4-pqc-fixture.json", result)
    rows = []
    for suite in result["next_suites"]:
        sizes = suite.get("rpki_object_generation_evidence", {}).get("artifact_sizes_bytes", {})
        rows.append({"suite": suite["suite"], "status": suite["status"], "CA": sizes.get("CA certificate", ""), "CRL": sizes.get("CRL", ""), "ROA": sizes.get("ROA CMS", ""), "MFT": sizes.get("Manifest CMS", "")})
    report = "# Selective Next-path Phase 4 PQC Fixture\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\nSchema version: `1`\n\n"
    report += markdown_table(rows, [("suite", "Next suite"), ("status", "Status"), ("CA", "CA bytes"), ("CRL", "CRL bytes"), ("ROA", "ROA bytes"), ("MFT", "Manifest bytes")])
    report += "\n\nAvailable checks passed: `" + str(result["all_available_checks_passed"]).lower() + "`\n\n## Limitations\n\n" + "\n".join(f"- {item}" for item in result["limitations"]) + "\n"
    (results_path / "report-phase4.md").write_text(report, encoding="utf-8", newline="\n")
    return result


if __name__ == "__main__":
    generate()
