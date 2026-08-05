from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from selective_next_path.rp_policy import RPTransitionPolicy
from selective_next_path.state import ComparisonScope, SemanticPayload
from tools.phase6_rp_policy import generate


PAYLOAD = SemanticPayload(resources={"ip_prefixes": ["192.0.2.0/25"], "as_ranges": [64496]}, vrps=[{"prefix": "192.0.2.0/25", "max_length": 25, "asn": 64496}])


class Phase6RPPolicyTest(unittest.TestCase):
    def test_end_to_end_policy(self):
        with tempfile.TemporaryDirectory() as name:
            result = generate(Path(name))
            self.assertTrue(result["all_checks_passed"])
            self.assertTrue(result["persisted_state_schema"]["activated"])
            self.assertTrue(result["persisted_state_schema"]["retired"])

    def test_restart_replay_conflict_and_no_fallback(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "state.json"
            policy = RPTransitionPolicy.create(path, "scope", "next-ta")
            self.assertTrue(policy.stage(1, "next-ta", PAYLOAD, PAYLOAD, ComparisonScope(), True)["accepted"])
            self.assertTrue(policy.activate(2)["accepted"])
            restarted = RPTransitionPolicy.load(path)
            self.assertEqual(restarted.activate(1)["reason"], "SEQUENCE_REPLAY")
            self.assertEqual(restarted.select(current_available=True, next_available=False, next_valid=False)["source"], "unavailable")
            self.assertEqual(restarted.retire(3)["reason"], "CURRENT_RETIRED")
            self.assertEqual(restarted.stage(4, "next-ta", PAYLOAD, PAYLOAD, ComparisonScope(), True)["reason"], "STATE_ROLLBACK")

    def test_ta_replacement_and_invalid_path(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "state.json"
            policy = RPTransitionPolicy.create(path, "scope", "next-ta")
            self.assertEqual(policy.stage(1, "other-ta", PAYLOAD, PAYLOAD, ComparisonScope(), True)["reason"], "NEXT_TA_REPLACEMENT_FORBIDDEN")
            self.assertEqual(policy.stage(2, "next-ta", PAYLOAD, PAYLOAD, ComparisonScope(), False)["reason"], "INVALID_NEXT_PARENT_PATH")
            self.assertTrue(policy.stage(1, "next-ta", PAYLOAD, PAYLOAD, ComparisonScope(), True)["accepted"])
            same = policy.stage(1, "next-ta", PAYLOAD, PAYLOAD, ComparisonScope(), True)
            self.assertEqual(same["reason"], "IDEMPOTENT_TRANSITION")
            changed = SemanticPayload(resources={"ip_prefixes": ["192.0.2.128/25"], "as_ranges": [64496]})
            self.assertEqual(policy.stage(1, "next-ta", PAYLOAD, changed, ComparisonScope(), True)["reason"], "SEQUENCE_CONFLICT")


if __name__ == "__main__":
    unittest.main()
