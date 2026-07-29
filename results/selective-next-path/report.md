# Selective Next-path Phase 1 Report

> EXPERIMENTAL / NOT FOR PRODUCTION

## Assumptions

- Protocol-neutral deterministic state-machine model only.
- No certificates, cryptography, RRDP, rsync, or validator behavior.
- The Current Suite is forgeable after the modeled compromise event; the pre-accepted Next TA remains secure.

## Scenario summary

- Accepted actions: 13
- Rejected actions: 4
- All assertions passed: `true`

| CA | State | Activated | Retired |
|---|---|---|---|
| delegated-prebuilt | activated | true | false |
| delegated-unprepared | current_only | false | false |
| hosted-a | activated | true | false |
| hosted-sibling | current_only | false | false |
| next-ta-2035 | next_ca_staged | false | false |
| rir-1 | next_ca_staged | false | false |

## Cost comparison

| Strategy | N | B | M | CA coverage | Resource coverage |
|---|---|---|---|---|---|
| all_cas_prebuilt | 6 | 6 | 2 | 1.0 | 1.0 |
| selective_upper_path | 6 | 3 | 2 | 0.833333 | 0.99 |
| mixed_tree_only | 6 | 0 | 2 | 0.0 | 0.0 |

## Security failures

| Step | Scope | Action | Reason |
|---|---|---|---|
| 11 | hosted-a | fetch_next | UNAVAILABLE_NEXT_NO_FALLBACK |
| 12 | global | accept_next_ta | CURRENT_SUITE_NOT_SECURE |
| 13 | hosted-sibling | create_next_ca | CURRENT_SIGNATURE_INSUFFICIENT_AFTER_COMPROMISE |
| 14 | delegated-unprepared | create_next_ca | UNPREPARED_DELEGATED_CA |

## Unsupported features

- Production RPKI validation or policy
- Real certificates, CMS, PQ signatures, Krill, Routinator, or rpki-client
- Secure out-of-band enrollment for an unprepared Delegated CA
- Byte-size, RRDP, rsync, HSM, repository, or timing measurements
- CCR as a protocol dependency

## Reproduction

```sh
make selective-next-path
make selective-next-path-test
```
