from __future__ import annotations

from typing import Any

from .state import CA, CARole, ManagementMode, NextPreparation, SCHEMA_VERSION, WARNING


def _coverage(cas: list[CA], covered: set[str]) -> dict[str, Any]:
    total_weight = sum(ca.resource_weight for ca in cas)
    covered_weight = sum(
        ca.resource_weight for ca in cas if ca.ca_id in covered
    )
    return {
        "ca_count": len(covered),
        "ca_count_fraction": round(len(covered) / len(cas), 6) if cas else 0,
        "resource_weight": covered_weight,
        "resource_weight_fraction": (
            round(covered_weight / total_weight, 6) if total_weight else 0
        ),
    }


def build_cost_model(
    cas: list[CA],
    concurrently_migrating: set[str],
) -> dict[str, Any]:
    ordered = sorted(cas, key=lambda ca: ca.ca_id)
    all_ids = {ca.ca_id for ca in ordered}
    prebuilt = {
        ca.ca_id
        for ca in ordered
        if ca.next_preparation is NextPreparation.PREBUILT
    }
    on_demand_hosted = {
        ca.ca_id
        for ca in ordered
        if (
            ca.management_mode is ManagementMode.HOSTED
            and ca.role is CARole.HOSTED
            and ca.next_preparation is NextPreparation.ON_DEMAND
            and ca.parent_ca_id in prebuilt
            and ca.authoritative_parent_ca_id == ca.parent_ca_id
            and ca.authoritative_registry_id is not None
        )
    }
    selective_covered = prebuilt | on_demand_hosted
    strategies = []
    for name, prepared, covered in (
        ("all_cas_prebuilt", all_ids, all_ids),
        ("selective_upper_path", prebuilt, selective_covered),
        ("mixed_tree_only", set(), set()),
    ):
        next_products = len(concurrently_migrating & covered)
        strategies.append(
            {
                "strategy": name,
                "N": len(ordered),
                "B": len(prepared),
                "M": len(concurrently_migrating),
                "prebuilt_key_count": len(prepared),
                "prebuilt_ca_certificate_count": len(prepared),
                "crl_count": len(prepared),
                "manifest_count": len(prepared),
                "on_demand_ca_count": len(on_demand_hosted)
                if name == "selective_upper_path"
                else 0,
                "current_signed_product_count": (
                    len(ordered) - next_products
                ),
                "next_signed_product_count": next_products,
                "post_compromise_migration_coverage": _coverage(
                    ordered,
                    covered,
                ),
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "warning": WARNING,
        "classification": (
            "synthetic Phase 1 count and coverage model; "
            "not operational measurement"
        ),
        "logical_ca_count": len(ordered),
        "prebuilt_ca_count": len(prebuilt),
        "concurrently_migrating_ca_count": len(concurrently_migrating),
        "strategies": strategies,
        "unsupported": [
            "byte-size estimates",
            "RRDP snapshot and delta estimates",
            "timing measurements",
        ],
    }
