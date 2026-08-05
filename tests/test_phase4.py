from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.phase4_pqc_fixture import generate


class Phase4PqcFixtureTest(unittest.TestCase):
    def test_mldsa_evidence_and_composite_boundary(self):
        with tempfile.TemporaryDirectory() as name:
            result = generate(Path(name))
            self.assertTrue(result["all_available_checks_passed"])
            mldsa, composite = result["next_suites"]
            self.assertEqual(mldsa["status"], "confirmed")
            self.assertEqual(mldsa["rpki_object_generation_evidence"]["artifact_sizes_bytes"]["ROA CMS"], 9434)
            self.assertEqual(composite["status"], "unsupported")
            self.assertIn("no Composite provider", composite["reason"])

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
