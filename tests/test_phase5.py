from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.phase5_hosted_workflow import generate


class Phase5HostedWorkflowTest(unittest.TestCase):
    def test_controller_contract_and_explicit_krill_boundary(self):
        with tempfile.TemporaryDirectory() as name:
            result = generate(Path(name))
            self.assertTrue(result["all_controller_checks_passed"])
            self.assertFalse(result["workflow"]["events"][-1]["current_fallback"])
            self.assertEqual(result["workflow"]["events"][3]["issuer"], "next-rir-1")
            if result["backend"]["krill"]["status"] == "skipped":
                self.assertEqual(result["krill_enforced_checks"], [])
                self.assertTrue(result["simulated_outside_krill"])

    def test_public_outputs_are_sanitized(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            generate(root)
            for path in root.iterdir():
                text = path.read_text(encoding="utf-8")
                self.assertIn("EXPERIMENTAL / NOT FOR PRODUCTION", text)
                self.assertNotIn("/Users/", text)
                self.assertNotIn("PRIVATE KEY", text)


if __name__ == "__main__":
    unittest.main()
