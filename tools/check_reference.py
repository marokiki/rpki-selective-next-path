#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference" / "pqc-rpki-lab"
EXPECTED_COMMIT = "0d572a851c29411bda4460e5c76394e6f4ec23c9"


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(REFERENCE), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def main() -> int:
    if not (REFERENCE / ".git").exists():
        print("reference check skipped: submodule is not initialized")
        return 0
    head = git("rev-parse", "HEAD")
    status = git("status", "--porcelain=v1")
    branch = git("symbolic-ref", "-q", "HEAD")
    failures = []
    if head.returncode or head.stdout.strip() != EXPECTED_COMMIT:
        failures.append("submodule HEAD does not match the pinned commit")
    if status.returncode or status.stdout:
        failures.append("submodule is dirty")
    if branch.returncode == 0:
        failures.append("submodule HEAD is not detached")
    if failures:
        for failure in failures:
            print(f"reference check failed: {failure}", file=sys.stderr)
        return 1
    print(f"reference check passed: detached {EXPECTED_COMMIT[:7]} and clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
