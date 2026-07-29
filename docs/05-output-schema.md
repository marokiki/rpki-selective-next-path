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
