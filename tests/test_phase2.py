from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from selective_next_path.phase2 import build_phase2_cost_model
from tools.phase2_cost_model import generate, load_inputs
from tools.selective_next_path_fixture import load_fixture, run_scenario


class Phase2CostModelTest(unittest.TestCase):
    def setUp(self):
        machine, _, _ = run_scenario(load_fixture())
        migrating = {ca_id for ca_id, state in machine.scopes.items() if state.activated and not state.retired}
        self.model = build_phase2_cost_model(list(machine.cas.values()), migrating, load_inputs())

    def row(self, name: str):
        return next(row for row in self.model["strategies"] if row["strategy"] == name)

    def test_formula_boundary_for_empty_mixed_tree(self):
        estimate = self.row("mixed_tree_only")["estimated_storage_and_transfer"]
        self.assertEqual((estimate["publication_object_count"], estimate["publication_bytes"]), (0, 0))
        self.assertEqual((estimate["rrdp_snapshot_bytes"], estimate["first_transition_rrdp_delta_bytes"]), (512, 384))

    def test_selective_B_is_smaller_than_N(self):
        row = self.row("selective_upper_path")
        self.assertEqual((row["N"], row["B"], row["M"]), (6, 3, 2))
        self.assertLess(row["B"], row["N"])

    def test_all_prebuilt_formula(self):
        estimate = self.row("all_cas_prebuilt")["estimated_storage_and_transfer"]
        self.assertEqual(estimate["publication_bytes"], 6 * (1064 + 415 + 1743) + 2 * 1621)
        self.assertEqual(estimate["publication_object_count"], 20)

    def test_selective_reduces_bytes_and_retains_weighted_coverage(self):
        all_row, selective = self.row("all_cas_prebuilt"), self.row("selective_upper_path")
        self.assertLess(selective["estimated_storage_and_transfer"]["publication_bytes"], all_row["estimated_storage_and_transfer"]["publication_bytes"])
        self.assertEqual(selective["post_compromise_migration_coverage"]["resource_weight_fraction"], 0.99)

    def test_outputs_are_deterministic_and_self_describing(self):
        with tempfile.TemporaryDirectory() as first_name, tempfile.TemporaryDirectory() as second_name:
            first, second = Path(first_name), Path(second_name)
            generate(first); generate(second)
            for name in ("cost-model-phase2.json", "experiment-manifest-phase2.json", "report-phase2.md"):
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())
                self.assertIn(b"EXPERIMENTAL / NOT FOR PRODUCTION", (first / name).read_bytes())
            parsed = json.loads((first / "cost-model-phase2.json").read_text())
            self.assertEqual((parsed["schema_version"], parsed["phase"]), (1, 2))


if __name__ == "__main__":
    unittest.main()
