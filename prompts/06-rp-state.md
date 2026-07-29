# Phase 6 prompt — RP transition and anti-rollback state

Implement a reference transition-policy layer around existing RP-produced outputs. Do not present it as a production validator.

Required state:

- accepted Next TA identifier;
- scoped CA or resource-class identifier;
- highest transition sequence;
- staged/activated/retired flags;
- last semantically matched resource, VRP, and ASPA digests.

Required behavior:

- before activation, Current is authoritative and Next may be compared;
- activation requires a valid Next path and semantic equivalence;
- after activation, Next is authoritative;
- Current may remain published but is not trusted for the activated scope;
- Next retrieval or validation failure after activation results in unavailable output, not Current fallback;
- older sequence/state is rejected after restart;
- retirement is monotonic.

Use deterministic fixture inputs and persist state in a documented JSON format under `local/` during tests. Commit only schemas, code, synthetic fixtures, and sanitized reports.
