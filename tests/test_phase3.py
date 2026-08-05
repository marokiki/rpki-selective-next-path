from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.phase3_real_fixture import generate


class Phase3RealFixtureTest(unittest.TestCase):
    def test_real_fixture_or_explicit_skip(self):
        with tempfile.TemporaryDirectory() as name:
            result = generate(Path(name))
            self.assertEqual(result["schema_version"], 1)
            self.assertIn(result["status"], {"confirmed", "skipped"})
            if result["status"] == "skipped":
                self.assertTrue(result["reason"])
                return
            self.assertTrue(result["all_checks_passed"])
            self.assertTrue(all(result["checks"].values()))
            self.assertFalse(result["private_keys_persisted"])
            self.assertEqual(result["suites"][0]["events"][2]["phase"], "pre_compromise")
            self.assertEqual(result["suites"][1]["events"][2]["phase"], "post_compromise")
            self.assertEqual(result["suites"][0]["roa_econtent_sha256"], result["suites"][1]["roa_econtent_sha256"])

    def test_public_outputs_do_not_disclose_paths_or_keys(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            generate(root)
            for path in root.iterdir():
                text = path.read_text(encoding="utf-8")
                self.assertIn("EXPERIMENTAL / NOT FOR PRODUCTION", text)
                self.assertNotIn("/Users/", text)
                self.assertNotIn("PRIVATE KEY", text)
            parsed = json.loads((root / "phase3-real-fixture.json").read_text())
            self.assertEqual(parsed["phase"], 3)


if __name__ == "__main__":
    unittest.main()
