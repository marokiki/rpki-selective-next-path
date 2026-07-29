# Phase 3 prompt — real RSA/P-256 fixtures

Build an end-to-end local fixture using existing repository object-generation and validation helpers.

Required lifecycle:

1. Generate independent Current RSA and Next P-256 trust roots.
2. Prebuild only Next TA → Next RIR/NIR.
3. Do not create the Hosted child in the Next hierarchy.
4. Publish and validate the Current Hosted child and Current ROA.
5. Mark Current as compromised in the experiment controller; this is a policy event, not a cryptographic exploit.
6. Create a new P-256 Hosted child under the already valid Next RIR/NIR.
7. Generate its CRL, Manifest, and semantically equivalent ROA.
8. Validate the Next path and VRP.
9. Demonstrate that the workflow uses no new Current-signed certificate to introduce the Next child.
10. Sanitize and publish only scripts, fixture metadata, validation summaries, and measurements.

All keys, generated repositories, and raw validator output remain below `local/`.

Add a network-free Makefile target that operates on existing local dependencies and records `skipped` with a reason when optional tooling is absent.
