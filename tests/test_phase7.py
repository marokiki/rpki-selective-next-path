from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.phase7_scale import generate


class Phase7ScaleTest(unittest.TestCase):
    def test_scale_formulas_and_recovery(self):
        with tempfile.TemporaryDirectory() as name:
            result = generate(Path(name))
            self.assertTrue(result["all_synthetic_checks_passed"])
            rows = result["synthetic_scale_results"]
            for n in (10, 100, 1000, 10000):
                full = next(row for row in rows if row["N"] == n and row["strategy"] == "all_cas_prebuilt")
                selective = next(row for row in rows if row["N"] == n and row["strategy"] == "selective_upper_path")
                self.assertLess(selective["B"], full["B"])
                self.assertEqual(selective["recovery"]["current_fallback_count"], 0)
                self.assertLess(selective["publication_bytes"], full["publication_bytes"])

    def test_krill_is_explicit_and_outputs_are_sanitized(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            result = generate(root)
            self.assertEqual(len(result["krill_backed_batches"]), 4)
            self.assertTrue(all(row["status"] in {"skipped", "not-run"} for row in result["krill_backed_batches"]))
            for path in root.iterdir():
                text = path.read_text(encoding="utf-8")
                self.assertIn("EXPERIMENTAL / NOT FOR PRODUCTION", text)
                self.assertNotIn("/Users/", text)


if __name__ == "__main__":
    unittest.main()
