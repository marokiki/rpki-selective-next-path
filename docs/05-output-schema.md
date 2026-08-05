# Output specification

All outputs go below `results/selective-next-path/`.

## topology.json

```json
{
  "schema_version": 1,
  "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
  "current_suite_state": "secure",
  "next_trust_anchor_state": "accepted",
  "cas": [],
  "relationships": []
}
```

Each CA record should include:

- `ca_id`
- `operator_id`
- `role`
- `management_mode`: `hosted` or `delegated`
- `parent_ca_id`
- `resource_weight`
- `current_state`
- `next_state`
- `next_preparation`: `prebuilt`, `on_demand`, or `none`
- `current_resources`
- `next_resources`

## scenario-results.json

Contains:

- scenario metadata;
- ordered input events;
- ordered event log;
- final state;
- accepted/rejected action counts;
- stable reason-code counts;
- assertions.

## cost-model.json

Contains at least:

- logical CA count `N`;
- prebuilt CA count `B`;
- concurrently migrating CA count `M`;
- prebuilt key count;
- prebuilt CA certificate count;
- CRL count;
- Manifest count;
- on-demand CA count;
- Current/Next signed-product counts;
- resource-weighted post-compromise migration coverage.

## report.md

Generated view only. It must state:

- experimental status;
- assumptions;
- scenario summary;
- cost comparison;
- security failures;
- unsupported features;
- commands required to reproduce the output.

## Phase 2-7 extension artifacts

- `cost-model-phase2.json` and `experiment-manifest-phase2.json`: deterministic size and RRDP-assumption model.
- `phase3-real-fixture.json`: local RSA/P-256 X.509, CRL, ROA, Manifest, and validation measurements.
- `phase4-pqc-fixture.json`: ML-DSA-65 generation/validation evidence and Composite support boundary.
- `phase5-hosted-workflow.json`: Hosted workflow controller contract and Krill enforcement boundary.
- `phase6-rp-policy.json`: persisted scoped activation, retirement, replay, and no-fallback evidence.
- `phase7-scale-evaluation.json`: calibrated synthetic scale rows and Krill batch execution status.

Every JSON artifact includes `schema_version` and classification or limitations. Phase 3, 4, and 7 timing values are measurements or projections as explicitly labeled and are not deterministic byte-for-byte outputs.
