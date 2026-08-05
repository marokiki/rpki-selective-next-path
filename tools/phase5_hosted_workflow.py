#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from selective_next_path.hosted_workflow import HostedWorkflow
from selective_next_path.result_io import markdown_table, write_json
from selective_next_path.state import SCHEMA_VERSION, WARNING

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "testdata" / "selective-next-path" / "phase5-hosted.json"
RESULTS = ROOT / "results" / "selective-next-path"


def probe_krill() -> dict[str, Any]:
    configured = os.environ.get("PQC_RPKI_KRILL_BIN", "")
    binary = configured or shutil.which("krill")
    if not binary:
        return {"status": "skipped", "reason": "Krill executable unavailable; set PQC_RPKI_KRILL_BIN", "network_used": False}
    result = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=30)
    return {"status": "available" if result.returncode == 0 else "failed", "version": (result.stdout or result.stderr).strip().splitlines()[0], "network_used": False}


def generate(results_path: Path = RESULTS) -> dict[str, Any]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    workflow = HostedWorkflow(fixture["parent_ca_id"], fixture["child_ca_id"], fixture["operator_id"], fixture["vrp"]).dry_run()
    krill = probe_krill()
    result = {
        "schema_version": SCHEMA_VERSION,
        "warning": WARNING,
        "phase": 5,
        "status": "simulated" if krill["status"] == "skipped" else "ready-for-krill-execution",
        "backend": {"krill": krill, "controller": "standalone dry-run orchestration contract"},
        "workflow": workflow,
        "all_controller_checks_passed": all(workflow["checks"].values()),
        "krill_enforced_checks": [],
        "simulated_outside_krill": ["Current compromise policy event", "child-absence assertion", "suite selection", "activation", "no-fallback behavior"],
        "required_krill_operations": ["create Hosted child under pre-existing Next parent", "issue resources", "publish CRL and Manifest", "publish equivalent ROA"],
        "limitations": [
            "Krill is unavailable in this environment, so no Krill state or repository was mutated.",
            "The workflow is a tested controller contract, not evidence that Krill enforces suite selection or no fallback.",
            "Phase 3 OpenSSL objects demonstrate the equivalent issuance shape but are not Krill-generated.",
            "Experimental RP executables are unavailable; no new RP acceptance evidence is produced.",
        ],
    }
    write_json(results_path / "phase5-hosted-workflow.json", result)
    rows = [{"step": row["step"], "event": row["event"], "accepted": str(row["accepted"]).lower()} for row in workflow["events"]]
    report = "# Selective Next-path Phase 5 Hosted Workflow\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\nSchema version: `1`\n\n"
    report += f"Krill status: **{krill['status']}**. Controller status: **{result['status']}**.\n\n"
    report += markdown_table(rows, [("step", "Step"), ("event", "Event"), ("accepted", "Accepted")])
    report += "\n\n## Limitations\n\n" + "\n".join(f"- {item}" for item in result["limitations"]) + "\n"
    (results_path / "report-phase5.md").write_text(report, encoding="utf-8", newline="\n")
    return result


if __name__ == "__main__":
    generate()
