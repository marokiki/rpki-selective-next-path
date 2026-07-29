from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from selective_next_path.model import TransitionModel
from selective_next_path.state import CAState, ReasonCode, SemanticPayload
from tools.selective_next_path_fixture import execute_event

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "testdata" / "selective-next-path" / "scenario.json"


def fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def prepare(data: dict | None = None) -> TransitionModel:
    data = data or fixture()
    model = TransitionModel.from_fixture(data)
    for event in data["events"][:6]:
        execute_event(model, event)
    return model


class AuthorizationAndRollbackGuardTest(unittest.TestCase):
    def test_authoritative_parent_must_match(self):
        data = copy.deepcopy(fixture())
        next(
            row for row in data["cas"] if row["ca_id"] == "hosted-a"
        )["authoritative_parent_ca_id"] = "next-ta-2035"
        result = prepare(data).create_next_ca("hosted-a", 1)
        self.assertEqual(
            result.reason_code,
            ReasonCode.AUTHORITATIVE_PARENT_MISMATCH,
        )

    def test_authoritative_registry_record_must_exist(self):
        data = copy.deepcopy(fixture())
        next(
            row for row in data["cas"] if row["ca_id"] == "hosted-a"
        )["authoritative_registry_id"] = "missing"
        result = prepare(data).create_next_ca("hosted-a", 1)
        self.assertEqual(
            result.reason_code,
            ReasonCode.AUTHORITATIVE_REGISTRY_RECORD_MISSING,
        )

    def test_authoritative_registry_resources_must_match(self):
        data = copy.deepcopy(fixture())
        next(
            row
            for row in data["registry_records"]
            if row["child_ca_id"] == "hosted-a"
        )["resources"]["ip_prefixes"] = ["198.51.100.0/24"]
        result = prepare(data).create_next_ca("hosted-a", 1)
        self.assertEqual(
            result.reason_code,
            ReasonCode.AUTHORITATIVE_REGISTRY_RECORD_MISMATCH,
        )

    def test_invalid_staged_objects_cannot_dual_publish(self):
        model = prepare()
        model.create_next_ca("hosted-a", 1)
        model.stage_next_ca(
            "hosted-a",
            2,
            model.cas["hosted-a"].current_semantics,
            objects_valid=False,
        )
        result = model.dual_publish("hosted-a", 3)
        self.assertEqual(result.reason_code, ReasonCode.NEXT_OBJECTS_INVALID)

    def test_child_delegation_mismatch_is_rejected(self):
        model = prepare()
        current = model.cas["delegated-prebuilt"].current_semantics
        candidate = SemanticPayload(
            resources=current.resources,
            vrps=current.vrps,
            aspas=current.aspas,
            child_delegations=[],
        )
        model.stage_next_ca("delegated-prebuilt", 2, candidate)
        model.dual_publish("delegated-prebuilt", 3)
        result = model.activate("delegated-prebuilt", 4)
        self.assertEqual(
            result.reason_code,
            ReasonCode.CHILD_DELEGATION_SEMANTICS_MISMATCH,
        )

    def test_lower_sequence_is_rejected_as_replay(self):
        model = prepare()
        model.create_next_ca("hosted-a", 1)
        model.stage_next_ca(
            "hosted-a",
            2,
            model.cas["hosted-a"].current_semantics,
        )
        result = model.apply_snapshot(
            "hosted-a",
            sequence=1,
            state=CAState.NEXT_PARENT_AVAILABLE,
            accepted_next_ta_id="next-ta-2035",
            next_semantics=SemanticPayload(),
            activated=False,
            retired=False,
        )
        self.assertEqual(result.reason_code, ReasonCode.SEQUENCE_REPLAY)

    def test_scope_cannot_change_accepted_next_ta(self):
        model = prepare()
        model.create_next_ca("hosted-a", 1)
        result = model.apply_snapshot(
            "hosted-a",
            sequence=2,
            state=CAState.NEXT_CA_STAGED,
            accepted_next_ta_id="next-ta-attacker",
            next_semantics=model.cas["hosted-a"].current_semantics,
            activated=False,
            retired=False,
        )
        self.assertEqual(
            result.reason_code,
            ReasonCode.NEXT_TA_REPLACEMENT_FORBIDDEN,
        )


if __name__ == "__main__":
    unittest.main()
