from __future__ import annotations

import unittest

from selective_next_path.semantics import (
    compare_payloads,
    normalize_resources,
    semantic_digest,
)
from selective_next_path.state import ComparisonScope, ReasonCode, SemanticPayload


class SemanticComparisonTest(unittest.TestCase):
    def test_resource_prefixes_and_as_ranges_are_canonical(self):
        left = {
            "ip_prefixes": ["192.0.2.1/24", "2001:0db8::/32"],
            "as_ranges": [[64496, 64497], [64498, 64500]],
        }
        right = {
            "ip_prefixes": ["2001:db8::/32", "192.0.2.0/24"],
            "as_ranges": [[64496, 64500]],
        }
        self.assertEqual(normalize_resources(left), normalize_resources(right))

    def test_vrp_order_and_provenance_fields_do_not_matter(self):
        current = SemanticPayload(
            resources={"ip_prefixes": [], "as_ranges": []},
            vrps=[
                {
                    "prefix": "192.0.2.0/24",
                    "maxLength": 24,
                    "asn": "AS64496",
                    "uri": "rsync://current.example/object.roa",
                }
            ],
        )
        candidate = SemanticPayload(
            resources={"as_ranges": [], "ip_prefixes": []},
            vrps=[
                {
                    "asn": 64496,
                    "max_length": 24,
                    "prefix": "192.0.2.1/24",
                    "validity": "different",
                }
            ],
        )
        equivalent, reason, _ = compare_payloads(
            current,
            candidate,
            ComparisonScope(),
        )
        self.assertTrue(equivalent)
        self.assertIsNone(reason)

    def test_both_absent_object_types_match(self):
        equivalent, reason, details = compare_payloads(
            SemanticPayload(),
            SemanticPayload(),
            ComparisonScope(resources=False, vrps=False, aspas=True),
        )
        self.assertTrue(equivalent)
        self.assertIsNone(reason)
        self.assertFalse(details["aspas"]["current_present"])

    def test_one_sided_object_type_is_mismatch(self):
        equivalent, reason, _ = compare_payloads(
            SemanticPayload(aspas=None),
            SemanticPayload(aspas=[]),
            ComparisonScope(resources=False, vrps=False, aspas=True),
        )
        self.assertFalse(equivalent)
        self.assertEqual(reason, ReasonCode.ASPA_SEMANTICS_MISMATCH)

    def test_disabled_object_type_is_ignored(self):
        equivalent, reason, _ = compare_payloads(
            SemanticPayload(aspas=[{"customer_asn": 1, "providers": [2]}]),
            SemanticPayload(aspas=None),
            ComparisonScope(resources=False, vrps=False, aspas=False),
        )
        self.assertTrue(equivalent)
        self.assertIsNone(reason)

    def test_aspa_provider_order_is_semantically_equal(self):
        current = SemanticPayload(
            aspas=[{"customer_asn": 64500, "providers": [64497, 64496]}]
        )
        candidate = SemanticPayload(
            aspas=[
                {"customer_asn": 64500, "provider_asns": [64496]},
                {"customer_asn": 64500, "provider_asns": [64497]},
            ]
        )
        equivalent, _, _ = compare_payloads(
            current,
            candidate,
            ComparisonScope(resources=False, vrps=False, aspas=True),
        )
        self.assertTrue(equivalent)

    def test_digest_uses_canonical_json_not_python_hash(self):
        self.assertEqual(
            semantic_digest({"b": 2, "a": 1}),
            semantic_digest({"a": 1, "b": 2}),
        )


if __name__ == "__main__":
    unittest.main()
