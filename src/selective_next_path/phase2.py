from __future__ import annotations

from typing import Any

from .cost import build_cost_model
from .state import CA, CARole, ManagementMode, NextPreparation, SCHEMA_VERSION, WARNING


def _publication_estimate(row: dict[str, Any], inputs: dict[str, Any], on_demand_generated: int = 0) -> dict[str, Any]:
    sizes = inputs["object_sizes_bytes"]
    per_ca = inputs["objects_per_ca"]
    rrdp = inputs["rrdp"]
    prepared = row["B"] + on_demand_generated
    next_products = row["next_signed_product_count"]
    object_counts = {
        "ca_certificates": prepared * per_ca["ca_certificate"],
        "crls": prepared * per_ca["crl"],
        "manifests": prepared * per_ca["manifest"],
        "signed_products": next_products * per_ca["signed_products"],
    }
    bytes_by_type = {
        "ca_certificates": object_counts["ca_certificates"] * sizes["ca_certificate"],
        "crls": object_counts["crls"] * sizes["crl"],
        "manifests": object_counts["manifests"] * sizes["manifest"],
        "signed_products": object_counts["signed_products"] * sizes["signed_product"],
    }
    publication_bytes = sum(bytes_by_type.values())
    publication_objects = sum(object_counts.values())
    return {
        "publication_object_count": publication_objects,
        "publication_bytes": publication_bytes,
        "rrdp_snapshot_bytes": publication_bytes + rrdp["snapshot_envelope_bytes"] + publication_objects * rrdp["snapshot_per_object_overhead_bytes"],
        "first_transition_rrdp_delta_bytes": publication_bytes + rrdp["delta_envelope_bytes"] + publication_objects * rrdp["delta_per_object_overhead_bytes"],
        "refresh_interval_seconds": inputs["refresh_interval_seconds"],
        "bytes_by_type": bytes_by_type,
        "object_counts": object_counts,
    }


def build_phase2_cost_model(cas: list[CA], concurrently_migrating: set[str], inputs: dict[str, Any]) -> dict[str, Any]:
    phase1 = build_cost_model(cas, concurrently_migrating)
    on_demand_migrating = sum(
        ca.ca_id in concurrently_migrating
        and ca.role is CARole.HOSTED
        and ca.management_mode is ManagementMode.HOSTED
        and ca.next_preparation is NextPreparation.ON_DEMAND
        for ca in cas
    )
    strategies = []
    for source_row in phase1["strategies"]:
        row = dict(source_row)
        generated = on_demand_migrating if row["strategy"] == "selective_upper_path" else 0
        row["on_demand_generated_ca_count"] = generated
        row["estimated_storage_and_transfer"] = _publication_estimate(row, inputs, generated)
        strategies.append(row)
    return {
        "schema_version": SCHEMA_VERSION,
        "warning": WARNING,
        "phase": 2,
        "classification": inputs["classification"],
        "simulation_epoch": inputs["simulation_epoch"],
        "parameters": {
            "N": phase1["logical_ca_count"],
            "B": phase1["prebuilt_ca_count"],
            "M": phase1["concurrently_migrating_ca_count"],
            "refresh_interval_seconds": inputs["refresh_interval_seconds"],
            "objects_per_ca": inputs["objects_per_ca"],
            "object_sizes_bytes": inputs["object_sizes_bytes"],
            "rrdp": inputs["rrdp"],
        },
        "source": inputs["source"],
        "formulas": {
            "publication_bytes": "sum(object_count[type] * object_size[type])",
            "rrdp_snapshot_bytes": "publication_bytes + snapshot_envelope_bytes + publication_object_count * snapshot_per_object_overhead_bytes",
            "first_transition_rrdp_delta_bytes": "publication_bytes + delta_envelope_bytes + changed_object_count * delta_per_object_overhead_bytes",
            "coverage": "covered CA count or resource weight divided by total",
        },
        "strategies": strategies,
        "limitations": [
            "RRDP envelope values are synthetic assumptions, not packet measurements.",
            "The first-transition delta assumes every modeled Next object is newly published.",
            "Refresh traffic, deduplication, compression, rsync, and timing are excluded.",
            "RSA fixture sizes are point samples and do not define all repository objects."
        ],
    }
