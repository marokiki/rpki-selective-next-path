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


def prepared_model() -> TransitionModel:
    data = fixture()
    model = TransitionModel.from_fixture(data)
    for event in data["events"][:6]:
        execute_event(model, event)
    return model


def activate_hosted(model: TransitionModel, ca_id: str = "hosted-a") -> None:
    model.create_next_ca(ca_id, 1)
    model.stage_next_ca(ca_id, 2, model.cas[ca_id].current_semantics)
    model.dual_publish(ca_id, 3)
    result = model.activate(ca_id, 4)
    if not result.accepted:
        raise AssertionError(result.reason_code)


class AcceptanceMatrixTest(unittest.TestCase):
    def test_t01_accept_next_ta_while_current_secure(self):
        model = TransitionModel.from_fixture(fixture())
        model.observe_next_ta("next-ta-2035")
        result = model.accept_next_ta("next-ta-2035")
        self.assertTrue(result.accepted)
        self.assertEqual(result.reason_code, ReasonCode.NEXT_TA_ACCEPTED)

    def test_t02_reject_new_next_ta_after_compromise(self):
        model = prepared_model()
        result = model.accept_next_ta("next-ta-attacker")
        self.assertFalse(result.accepted)
        self.assertEqual(
            result.reason_code,
            ReasonCode.CURRENT_SUITE_NOT_SECURE,
        )

    def test_t03_prebuild_rir_before_compromise(self):
        data = fixture()
        model = TransitionModel.from_fixture(data)
        for event in data["events"][:4]:
            result = execute_event(model, event)
        self.assertTrue(result.accepted)
        self.assertEqual(model.scopes["rir-1"].state, CAState.NEXT_CA_STAGED)

    def test_t04_create_hosted_after_compromise_under_next_parent(self):
        model = prepared_model()
        result = model.create_next_ca("hosted-a", 1)
        self.assertTrue(result.accepted)
        self.assertEqual(result.reason_code, ReasonCode.NEXT_CA_CREATED)

    def test_t05_reject_hosted_under_current_only_parent(self):
        model = TransitionModel.from_fixture(fixture())
        model.observe_next_ta("next-ta-2035")
        model.accept_next_ta("next-ta-2035")
        model.compromise_current()
        result = model.create_next_ca("hosted-a", 1)
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason_code, ReasonCode.INVALID_NEXT_PARENT_PATH)

    def test_t06_allow_prebuilt_delegated_after_compromise(self):
        model = prepared_model()
        self.assertEqual(
            model.scopes["delegated-prebuilt"].state,
            CAState.NEXT_CA_STAGED,
        )
        model.dual_publish("delegated-prebuilt", 2)
        result = model.activate("delegated-prebuilt", 3)
        self.assertTrue(result.accepted)

    def test_t07_reject_unprepared_delegated_after_compromise(self):
        model = prepared_model()
        result = model.create_next_ca("delegated-unprepared", 1)
        self.assertFalse(result.accepted)
        self.assertEqual(
            result.reason_code,
            ReasonCode.UNPREPARED_DELEGATED_CA,
        )

    def test_t08_reject_resource_mismatch(self):
        model = prepared_model()
        model.create_next_ca("hosted-a", 1)
        source = model.cas["hosted-a"].current_semantics
        candidate = SemanticPayload(
            resources={"ip_prefixes": ["198.51.100.0/24"], "as_ranges": []},
            vrps=source.vrps,
        )
        model.stage_next_ca("hosted-a", 2, candidate)
        model.dual_publish("hosted-a", 3)
        result = model.activate("hosted-a", 4)
        self.assertEqual(
            result.reason_code,
            ReasonCode.RESOURCE_SEMANTICS_MISMATCH,
        )

    def test_t09_reject_vrp_mismatch(self):
        model = prepared_model()
        model.create_next_ca("hosted-a", 1)
        source = model.cas["hosted-a"].current_semantics
        candidate = SemanticPayload(
            resources=source.resources,
            vrps=[
                {
                    "prefix": "192.0.2.0/25",
                    "max_length": 25,
                    "asn": 64499,
                }
            ],
        )
        model.stage_next_ca("hosted-a", 2, candidate)
        model.dual_publish("hosted-a", 3)
        result = model.activate("hosted-a", 4)
        self.assertEqual(
            result.reason_code,
            ReasonCode.VRP_SEMANTICS_MISMATCH,
        )

    def test_t10_reject_aspa_mismatch(self):
        model = prepared_model()
        source = model.cas["delegated-prebuilt"].current_semantics
        candidate = SemanticPayload(
            resources=source.resources,
            vrps=source.vrps,
            aspas=[{"customer_asn": 64500, "provider_asns": [64496]}],
            child_delegations=source.child_delegations,
        )
        model.stage_next_ca("delegated-prebuilt", 2, candidate)
        model.dual_publish("delegated-prebuilt", 3)
        result = model.activate("delegated-prebuilt", 4)
        self.assertEqual(
            result.reason_code,
            ReasonCode.ASPA_SEMANTICS_MISMATCH,
        )

    def test_t11_activate_equivalent_hosted_scope(self):
        model = prepared_model()
        activate_hosted(model)
        self.assertTrue(model.scopes["hosted-a"].activated)

    def test_t12_next_failure_before_activation_keeps_current(self):
        model = prepared_model()
        result = model.fetch_next("hosted-sibling", available=False)
        self.assertTrue(result.accepted)
        self.assertEqual(
            result.reason_code,
            ReasonCode.CURRENT_REMAINS_AUTHORITATIVE,
        )

    def test_t13_next_failure_after_activation_has_no_fallback(self):
        model = prepared_model()
        activate_hosted(model)
        result = model.fetch_next("hosted-a", available=False)
        self.assertFalse(result.accepted)
        self.assertEqual(
            result.reason_code,
            ReasonCode.UNAVAILABLE_NEXT_NO_FALLBACK,
        )

    def test_t14_reject_pre_activation_snapshot_after_activation(self):
        model = prepared_model()
        activate_hosted(model)
        result = model.apply_snapshot(
            "hosted-a",
            sequence=5,
            state=CAState.DUAL_PUBLISHED,
            accepted_next_ta_id="next-ta-2035",
            next_semantics=model.cas["hosted-a"].current_semantics,
            activated=False,
            retired=False,
        )
        self.assertEqual(result.reason_code, ReasonCode.STATE_ROLLBACK)

    def test_t15_reject_current_replay_after_retirement(self):
        model = prepared_model()
        activate_hosted(model)
        model.retire_current("hosted-a", 5)
        result = model.apply_snapshot(
            "hosted-a",
            sequence=6,
            state=CAState.ACTIVATED,
            accepted_next_ta_id="next-ta-2035",
            next_semantics=model.cas["hosted-a"].current_semantics,
            activated=True,
            retired=False,
        )
        self.assertEqual(
            result.reason_code,
            ReasonCode.CURRENT_REINTRODUCTION_AFTER_RETIREMENT,
        )

    def test_t16_sibling_remains_current(self):
        model = prepared_model()
        activate_hosted(model)
        self.assertEqual(
            model.scopes["hosted-sibling"].state,
            CAState.CURRENT_ONLY,
        )

    def test_t17_batch_hosted_creation_is_deterministic(self):
        first = prepared_model()
        second = prepared_model()
        first_results = [
            first.create_next_ca(ca_id, 1).to_dict()
            for ca_id in ("hosted-a", "hosted-sibling")
        ]
        second_results = [
            second.create_next_ca(ca_id, 1).to_dict()
            for ca_id in ("hosted-a", "hosted-sibling")
        ]
        self.assertEqual(first_results, second_results)
        self.assertTrue(all(row["accepted"] for row in first_results))

    def test_t18_restart_preserves_anti_rollback_state(self):
        data = fixture()
        model = prepared_model()
        activate_hosted(model)
        restored = TransitionModel.restore(data, model.export_state())
        result = restored.apply_snapshot(
            "hosted-a",
            sequence=3,
            state=CAState.DUAL_PUBLISHED,
            accepted_next_ta_id="next-ta-2035",
            next_semantics=restored.cas["hosted-a"].current_semantics,
            activated=False,
            retired=False,
        )
        self.assertEqual(result.reason_code, ReasonCode.STATE_ROLLBACK)

    def test_current_signed_introduction_after_compromise_is_rejected(self):
        model = prepared_model()
        result = model.create_next_ca(
            "hosted-sibling",
            1,
            current_signature_only=True,
        )
        self.assertEqual(
            result.reason_code,
            ReasonCode.CURRENT_SIGNATURE_INSUFFICIENT_AFTER_COMPROMISE,
        )

    def test_hosted_operator_mismatch_is_rejected(self):
        data = copy.deepcopy(fixture())
        next(
            row for row in data["cas"] if row["ca_id"] == "hosted-a"
        )["operator_id"] = "attacker"
        model = TransitionModel.from_fixture(data)
        for event in data["events"][:6]:
            execute_event(model, event)
        result = model.create_next_ca("hosted-a", 1)
        self.assertEqual(
            result.reason_code,
            ReasonCode.AUTHORITATIVE_HOSTED_OPERATOR_MISMATCH,
        )

    def test_equal_sequence_is_idempotent_or_conflicting(self):
        model = prepared_model()
        first = model.create_next_ca("hosted-a", 1)
        same = model.create_next_ca("hosted-a", 1)
        conflict = model.stage_next_ca(
            "hosted-a",
            1,
            model.cas["hosted-a"].current_semantics,
        )
        self.assertTrue(first.accepted)
        self.assertEqual(same.reason_code, ReasonCode.IDEMPOTENT_TRANSITION)
        self.assertEqual(conflict.reason_code, ReasonCode.SEQUENCE_CONFLICT)

    def test_accepted_ta_cannot_be_replaced_while_secure(self):
        model = TransitionModel.from_fixture(fixture())
        model.observe_next_ta("next-ta-2035")
        model.accept_next_ta("next-ta-2035")
        result = model.observe_next_ta("next-ta-attacker")
        self.assertEqual(
            result.reason_code,
            ReasonCode.NEXT_TA_REPLACEMENT_FORBIDDEN,
        )


if __name__ == "__main__":
    unittest.main()
