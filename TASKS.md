# Implementation backlog

## Phase 0 — Repository inspection and plan

- Map existing mixed-tree, key-roll, RPKI object, Krill, and RP integration code.
- Identify reusable helpers and avoid duplicate object models.
- Produce a file-by-file implementation plan.
- Do not change code in Ask/plan mode.

## Phase 1 — Deterministic state-machine model

- Add a protocol-neutral model under `src/pqc_rpki_lab/`.
- Model CA roles, Current compromise, Next TA acceptance, prebuilt paths, on-demand Hosted CA creation, staging, activation, retirement, and rollback rejection.
- Add synthetic topology and scenario runner.
- Add Makefile targets and unit tests.
- Produce JSON and Markdown outputs.

## Phase 2 — Cost and coverage model

- Count prebuilt keys, certificates, CRLs, Manifests, on-demand CAs, and signed products.
- Support logical-CA count and resource-weighted coverage.
- Compare:
  - all-CAs prebuilt,
  - selective upper-path prebuild,
  - Mixed-Tree only.
- Add deterministic scenario inputs and reports.

## Phase 3 — Real RSA/P-256 fixtures

- Generate two independent trust roots.
- Prebuild Next TA → RIR/NIR.
- Keep Hosted child absent before compromise.
- After simulated compromise, issue a P-256 Hosted CA and ROA only from the Next parent.
- Validate with existing local tooling.
- Keep all keys and generated repositories below `local/`; commit only scripts and sanitized summaries.

## Phase 4 — ML-DSA / Composite fixtures

- Reuse pinned OpenSSL and provider paths.
- Replace the P-256 Next Suite with ML-DSA-65 and the selected Composite suite.
- Validate with the existing experimental rpki-client and Routinator paths.
- Record unsupported cases explicitly.

## Phase 5 — Krill Hosted workflow

- Extend the experimental Krill integration to model an authoritative Hosted backend.
- Create a Hosted CA after Current compromise under the prebuilt Next parent.
- Publish CRL, Manifest, and ROA.
- Avoid claiming production compatibility.

## Phase 6 — RP transition state

- Prototype scoped activation and no-fallback state.
- Persist monotonic transition state.
- Reject Current replay after activation.
- Test Next repository failure after activation as unavailable, not fallback.

## Phase 7 — Scale evaluation

- Run synthetic and Krill-backed batch sizes.
- Measure generation time, publication size, RP validation time, and recovery behavior.
- Compare full prebuild, selective prebuild, and Mixed-Tree-only baselines.
