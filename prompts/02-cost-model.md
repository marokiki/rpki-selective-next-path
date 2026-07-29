# Phase 2 prompt — cost and migration coverage

Extend the Phase 1 model with a deterministic cost and coverage estimator.

Compare:

A. all logical CAs prebuilt;
B. selective prebuild of TA, RIR/NIR, and Delegated operators, with Hosted CAs created on demand;
C. Mixed-Tree-only preparation.

Use explicit input variables:

- `N`: logical CA count;
- `B`: prebuilt Next CA count;
- `M`: currently migrating CA count;
- per-CA resource weights;
- per-object byte sizes supplied by a JSON input;
- refresh interval assumptions.

Produce machine-readable counts and estimated bytes for:

- Next CA keys;
- CA certificates;
- CRLs;
- Manifests;
- Hosted CAs generated on demand;
- signed products;
- RRDP snapshot/delta first-order estimates;
- post-compromise migration coverage by CA count and resource weight.

Keep estimates clearly marked as synthetic. Reuse measured object-size inputs already present in the repository where appropriate, but preserve source/classification metadata.

Add tests for formulas, boundary cases, and `B << N` scenarios. Do not claim global operational values without measured input.
