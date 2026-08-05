# Selective Next-path Phase 2 Cost Model

> EXPERIMENTAL / NOT FOR PRODUCTION

Schema version: `1`

The model combines deterministic Phase 1 topology counts with public RSA object-size measurements and explicit synthetic RRDP overhead assumptions. Byte values are estimates, not transfer measurements.

| Strategy | N | B | M | On-demand CA | Published bytes | RRDP snapshot bytes | First delta bytes | CA coverage | Resource coverage |
|---|---|---|---|---|---|---|---|---|---|
| all_cas_prebuilt | 6 | 6 | 2 | 0 | 22574 | 25006 | 25518 | 1.0 | 1.0 |
| mixed_tree_only | 6 | 0 | 2 | 0 | 0 | 512 | 384 | 0.0 | 0.0 |
| selective_upper_path | 6 | 3 | 2 | 1 | 16130 | 17986 | 18306 | 0.833333 | 0.99 |

## Classification and limitations

- RRDP envelope values are synthetic assumptions, not packet measurements.
- The first-transition delta assumes every modeled Next object is newly published.
- Refresh traffic, deduplication, compression, rsync, and timing are excluded.
- RSA fixture sizes are point samples and do not define all repository objects.
