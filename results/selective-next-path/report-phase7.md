# Selective Next-path Phase 7 Scale Evaluation

> EXPERIMENTAL / NOT FOR PRODUCTION

Schema version: `1`

| N | Strategy | B | M | Projected bytes | CA coverage | Current fallbacks |
|---|---|---|---|---|---|---|
| 10 | all_cas_prebuilt | 10 | 1 | 18208 | 1.0 | 0 |
| 10 | selective_upper_path | 1 | 1 | 4352 | 0.9 | 0 |
| 10 | mixed_tree_only | 0 | 1 | 0 | 0.0 | 0 |
| 100 | all_cas_prebuilt | 100 | 10 | 182080 | 1.0 | 0 |
| 100 | selective_upper_path | 10 | 10 | 43520 | 0.82 | 0 |
| 100 | mixed_tree_only | 0 | 10 | 0 | 0.0 | 0 |
| 1000 | all_cas_prebuilt | 1000 | 100 | 1820800 | 1.0 | 0 |
| 1000 | selective_upper_path | 100 | 100 | 435200 | 0.82 | 0 |
| 1000 | mixed_tree_only | 0 | 100 | 0 | 0.0 | 0 |
| 10000 | all_cas_prebuilt | 10000 | 1000 | 18208000 | 1.0 | 0 |
| 10000 | selective_upper_path | 1000 | 1000 | 4352000 | 0.82 | 0 |
| 10000 | mixed_tree_only | 0 | 1000 | 0 | 0.0 | 0 |

Synthetic checks passed: `true`

Krill-backed batches: **skipped**

## Limitations

- Scale values are linear projections from one Phase 3 P-256 run; they are not batch cryptographic measurements.
- ML-DSA evidence is recorded in Phase 4 but is not used for timing projection because comparable validation timing is unavailable.
- Krill-backed batches were skipped because no isolated Krill executable/repository is configured.
- RRDP, rsync, caching, concurrency, HSM behavior, and validator memory are not modeled.
