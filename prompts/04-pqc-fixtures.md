# Phase 4 prompt — ML-DSA and Composite fixtures

Replace the P-256 Next Suite from Phase 3 with:

- pure ML-DSA-65;
- id-MLDSA65-ECDSA-P256-SHA512 using the repository's pinned Composite provider.

Reuse the existing OpenSSL, Composite provider, rpki-client, Routinator/rpki-rs, and fixture-generation paths. Do not create a second incompatible provider integration.

Measure:

- Hosted CA creation;
- CA certificate, CRL, Manifest, and ROA sizes;
- generation time;
- validation time;
- RP acceptance matrix;
- negative cases.

Keep Current-Suite compromise as a policy state in the controller. Do not claim that the experiment performs an RSA break.

The public report must distinguish:

- cryptographic implementation reuse;
- RPKI object generation evidence;
- RP interoperability evidence;
- synthetic transition-policy evidence.
