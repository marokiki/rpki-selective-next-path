from __future__ import annotations

import hashlib
import ipaddress
import json
from typing import Any

from .state import ComparisonScope, ReasonCode, SemanticPayload


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def semantic_digest(value: Any | None) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def normalize_as_ranges(values: list[Any]) -> list[list[int]]:
    ranges: list[tuple[int, int]] = []
    for value in values:
        if isinstance(value, int):
            start = end = value
        elif isinstance(value, str):
            parts = value.removeprefix("AS").split("-", 1)
            start = int(parts[0].removeprefix("AS"))
            end = int(parts[-1].removeprefix("AS"))
        else:
            start, end = (int(item) for item in value)
        if start > end:
            raise ValueError(f"invalid AS range: {value}")
        ranges.append((start, end))
    merged: list[list[int]] = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def normalize_resources(value: dict[str, Any]) -> dict[str, Any]:
    prefixes = {
        str(ipaddress.ip_network(prefix, strict=False))
        for prefix in value.get("ip_prefixes", [])
    }
    return {
        "ip_prefixes": sorted(
            prefixes,
            key=lambda item: (
                ipaddress.ip_network(item).version,
                int(ipaddress.ip_network(item).network_address),
                ipaddress.ip_network(item).prefixlen,
            ),
        ),
        "as_ranges": normalize_as_ranges(value.get("as_ranges", [])),
    }


def normalize_vrps(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = {
        (
            str(ipaddress.ip_network(row["prefix"], strict=False)),
            int(row.get("max_length", row.get("maxLength"))),
            int(str(row["asn"]).removeprefix("AS")),
        )
        for row in values
    }
    return [
        {"prefix": prefix, "max_length": max_length, "asn": asn}
        for prefix, max_length, asn in sorted(
            normalized,
            key=lambda row: (
                ipaddress.ip_network(row[0]).version,
                int(ipaddress.ip_network(row[0]).network_address),
                ipaddress.ip_network(row[0]).prefixlen,
                row[1],
                row[2],
            ),
        )
    ]


def normalize_aspas(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_customer: dict[int, set[int]] = {}
    for row in values:
        customer = int(str(row["customer_asn"]).removeprefix("AS"))
        providers = {
            int(str(provider).removeprefix("AS"))
            for provider in row.get("provider_asns", row.get("providers", []))
        }
        by_customer.setdefault(customer, set()).update(providers)
    return [
        {"customer_asn": customer, "provider_asns": sorted(providers)}
        for customer, providers in sorted(by_customer.items())
    ]


def normalize_child_delegations(
    values: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    normalized = [
        {
            "child_ca_id": row["child_ca_id"],
            "resources": normalize_resources(row["resources"]),
        }
        for row in values
    ]
    return sorted(
        normalized,
        key=lambda row: (row["child_ca_id"], canonical_json(row["resources"])),
    )


def canonical_payload(payload: SemanticPayload) -> dict[str, Any]:
    return {
        "resources": (
            None
            if payload.resources is None
            else normalize_resources(payload.resources)
        ),
        "vrps": None if payload.vrps is None else normalize_vrps(payload.vrps),
        "aspas": None if payload.aspas is None else normalize_aspas(payload.aspas),
        "child_delegations": (
            None
            if payload.child_delegations is None
            else normalize_child_delegations(payload.child_delegations)
        ),
    }


def payload_digests(payload: SemanticPayload) -> dict[str, str | None]:
    canonical = canonical_payload(payload)
    return {
        key: semantic_digest(value)
        for key, value in canonical.items()
    }


def compare_payloads(
    current: SemanticPayload,
    candidate: SemanticPayload,
    scope: ComparisonScope,
) -> tuple[bool, ReasonCode | None, dict[str, dict[str, Any]]]:
    current_value = canonical_payload(current)
    candidate_value = canonical_payload(candidate)
    checks = (
        ("resources", scope.resources, ReasonCode.RESOURCE_SEMANTICS_MISMATCH),
        ("vrps", scope.vrps, ReasonCode.VRP_SEMANTICS_MISMATCH),
        ("aspas", scope.aspas, ReasonCode.ASPA_SEMANTICS_MISMATCH),
        (
            "child_delegations",
            scope.child_delegations,
            ReasonCode.CHILD_DELEGATION_SEMANTICS_MISMATCH,
        ),
    )
    details: dict[str, dict[str, Any]] = {}
    for name, enabled, reason in checks:
        left = current_value[name]
        right = candidate_value[name]
        equivalent = not enabled or left == right
        details[name] = {
            "enabled": enabled,
            "current_present": left is not None,
            "next_present": right is not None,
            "equivalent": equivalent,
        }
        if enabled and not equivalent:
            return False, reason, details
    return True, None, details
