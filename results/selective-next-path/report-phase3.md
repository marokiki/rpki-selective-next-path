# Selective Next-path Phase 3 Real Fixture

> EXPERIMENTAL / NOT FOR PRODUCTION

Schema version: `1`

Status: **confirmed**

| Suite | Algorithm | Hosted CA bytes | ROA bytes | Manifest bytes |
|---|---|---|---|---|
| current | RSA-2048/SHA-256 | 996 | 1483 | 1554 |
| next | P-256/SHA-256 | 595 | 888 | 960 |

All checks passed: `true`

## Limitations

- P-256 is a classical stand-in for the Next Suite, not a PQC algorithm.
- Validation uses OpenSSL path/CMS checks and the pinned manifest parser, not an independent production RP.
- Timing values are single-run wall-clock measurements and require repeated sampling before statistical use.
- No RRDP or rsync transport is exercised.
