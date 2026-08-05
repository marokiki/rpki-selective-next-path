# Selective Next-path Phase 5 Hosted Workflow

> EXPERIMENTAL / NOT FOR PRODUCTION

Schema version: `1`

Krill status: **skipped**. Controller status: **simulated**.

| Step | Event | Accepted |
|---|---|---|
| 1 | next_parent_ready | true |
| 2 | assert_hosted_child_absent | true |
| 3 | mark_current_compromised | true |
| 4 | create_hosted_child | true |
| 5 | publish | true |
| 6 | activate | true |
| 7 | next_unavailable | true |

## Limitations

- Krill is unavailable in this environment, so no Krill state or repository was mutated.
- The workflow is a tested controller contract, not evidence that Krill enforces suite selection or no fallback.
- Phase 3 OpenSSL objects demonstrate the equivalent issuance shape but are not Krill-generated.
- Experimental RP executables are unavailable; no new RP acceptance evidence is produced.
