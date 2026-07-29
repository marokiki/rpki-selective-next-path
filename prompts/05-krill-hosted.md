# Phase 5 prompt — Krill Hosted workflow

Inspect the existing experimental Krill patch and scripts before changing them.

Prototype the smallest Krill-backed workflow that demonstrates:

- a pre-existing Next RIR/NIR parent;
- an absent Hosted child before the transition event;
- creation of a Hosted child after the controller marks Current compromised;
- issuance from the Next parent only;
- publication of CRL, Manifest, and ROA;
- validation by the existing experimental RP paths;
- no Current fallback after activation in the experiment controller.

Do not implement a production emergency migration API. Keep suite selectors, private keys, Krill state, repositories, logs, and external checkouts below `local/`. Commit only minimal patches, orchestration scripts, tests, and sanitized result summaries.

Add explicit limitations for any Krill behavior that is simulated outside Krill rather than enforced by Krill itself.
