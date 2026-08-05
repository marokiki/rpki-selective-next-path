# Selective Next-path Phase 6 RP Policy

> EXPERIMENTAL / NOT FOR PRODUCTION

Schema version: `1`

| Event | Selected source | Accepted | Reason |
|---|---|---|---|
| select_before | current |  | CURRENT_AUTHORITATIVE_BEFORE_ACTIVATION |
| stage |  | True | NEXT_OUTPUT_STAGED |
| activate |  | True | SCOPE_ACTIVATED |
| select_after | next |  | NEXT_AUTHORITATIVE_AFTER_ACTIVATION |
| next_outage | unavailable |  | UNAVAILABLE_NEXT_NO_FALLBACK |
| restart_replay |  | False | SEQUENCE_REPLAY |
| retire |  | True | CURRENT_RETIRED |
| current_remains_published | next |  | NEXT_AUTHORITATIVE_AFTER_ACTIVATION |

All checks passed: `true`

## Limitations

- This is a reference policy layer around RP-like semantic outputs, not a production validator.
- Certificate and repository validation results are inputs to the policy rather than performed by it.
- Persistence uses a single JSON file and does not provide transactional multi-process locking.
