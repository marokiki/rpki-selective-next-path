# Selective Next-path Phase 4 PQC Fixture

> EXPERIMENTAL / NOT FOR PRODUCTION

Schema version: `1`

| Next suite | Status | CA bytes | CRL bytes | ROA bytes | Manifest bytes |
|---|---|---|---|---|---|
| ML-DSA-65 | confirmed | 5793 | 3464 | 9434 | 9556 |
| id-MLDSA65-ECDSA-P256-SHA512 | unsupported |  |  |  |  |

Available checks passed: `true`

## Limitations

- The fresh probe measures aggregate CA/EE/CRL/CMS-attempt runtime, not isolated Hosted CA latency.
- Complete ML-DSA ROA and Manifest sizes and validation reuse pinned public evidence.
- Unmodified Routinator, rpki-client, and FORT rejected the ML-DSA repository; no RP acceptance is claimed.
- The requested Composite suite remains unsupported without the pinned provider and RPKI profile path.
