from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from selective_next_path.cost import build_cost_model
from tools.selective_next_path_fixture import generate, load_fixture, run_scenario


class CostAndOutputTest(unittest.TestCase):
    def setUp(self):
        self.fixture = load_fixture()
        self.model, self.scenario, self.cost = run_scenario(self.fixture)

    def test_t19_all_cas_prebuilt_counts(self):
        row = next(
            row
            for row in self.cost["strategies"]
            if row["strategy"] == "all_cas_prebuilt"
        )
        self.assertEqual(row["N"], 6)
        self.assertEqual(row["B"], 6)
        self.assertEqual(row["prebuilt_key_count"], 6)
        self.assertEqual(
            row["post_compromise_migration_coverage"]["ca_count_fraction"],
            1.0,
        )

    def test_t20_selective_prebuild_counts_and_coverage(self):
        row = next(
            row
            for row in self.cost["strategies"]
            if row["strategy"] == "selective_upper_path"
        )
        self.assertEqual(row["N"], 6)
        self.assertEqual(row["B"], 3)
        self.assertEqual(row["M"], 2)
        self.assertEqual(row["on_demand_ca_count"], 2)
        self.assertEqual(
            row["post_compromise_migration_coverage"]["ca_count_fraction"],
            0.833333,
        )
        self.assertEqual(
            row["post_compromise_migration_coverage"][
                "resource_weight_fraction"
            ],
            0.99,
        )

    def test_cost_model_is_independent_of_ca_input_order(self):
        expected = build_cost_model(
            list(self.model.cas.values()),
            {"hosted-a", "delegated-prebuilt"},
        )
        actual = build_cost_model(
            list(reversed(self.model.cas.values())),
            {"delegated-prebuilt", "hosted-a"},
        )
        self.assertEqual(actual, expected)

    def test_scenario_assertions_pass(self):
        self.assertTrue(self.scenario["all_assertions_passed"])
        self.assertTrue(all(self.scenario["assertions"].values()))

    def test_outputs_are_byte_for_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as first_name:
            with tempfile.TemporaryDirectory() as second_name:
                first = Path(first_name)
                second = Path(second_name)
                generate(results_path=first)
                generate(results_path=second)
                for name in (
                    "topology.json",
                    "scenario-results.json",
                    "cost-model.json",
                    "report.md",
                ):
                    self.assertEqual(
                        (first / name).read_bytes(),
                        (second / name).read_bytes(),
                    )

    def test_outputs_have_warning_schema_and_no_host_paths(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            generate(results_path=root)
            for path in sorted(root.iterdir()):
                text = path.read_text(encoding="utf-8")
                self.assertIn("EXPERIMENTAL / NOT FOR PRODUCTION", text)
                self.assertNotIn("/" + "Users/", text)
                self.assertNotIn("PRIVATE KEY", text)
                self.assertTrue(text.endswith("\n"))
            for name in (
                "topology.json",
                "scenario-results.json",
                "cost-model.json",
            ):
                value = json.loads((root / name).read_text())
                self.assertEqual(value["schema_version"], 1)


if __name__ == "__main__":
    unittest.main()
