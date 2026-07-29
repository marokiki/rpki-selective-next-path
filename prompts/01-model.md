# Phase 1 prompt — state-machine model

Implement Phase 1 from `codex/selective-next-path/TASKS.md`.

Scope this task to a pure Python deterministic model. Do not generate real certificates and do not modify Krill, Routinator, rpki-client, or OpenSSL integration.

Required scenarios:

1. Pre-accept a Next Trust Anchor while Current is secure.
2. Prebuild Next TA → Next RIR/NIR.
3. Leave Hosted CA A absent from the Next hierarchy.
4. Mark Current Suite compromised.
5. Create Hosted CA A under the valid Next RIR/NIR using the modeled authoritative Hosted operator.
6. Stage equivalent resources and VRPs.
7. Activate Hosted CA A and forbid Current fallback.
8. Reject a new Next TA after compromise.
9. Reject a Current-signed introduction of a new Next CA key after compromise.
10. Reject migration of an unprepared Delegated CA.
11. Allow a separately prebuilt Delegated CA to activate.
12. Keep a sibling Hosted CA on Current.

Add focused unit tests with stable reason codes. Add deterministic JSON fixtures and generated Markdown. Add `make selective-next-path` and `make selective-next-path-test`.

Do not add CCR as a dependency. Do not compare raw DER. Use modeled resource and payload semantics.

Run the new focused tests and the repository-wide test target. Report all results.
