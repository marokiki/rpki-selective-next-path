# Codex master prompt

You are working in the `marokiki/pqc-rpki-lab` repository.

Read these files before changing code:

- repository `README.md`
- repository `Makefile`
- `codex/selective-next-path/AGENTS.md`
- `codex/selective-next-path/docs/01-design.md`
- `codex/selective-next-path/docs/02-threat-model.md`
- `codex/selective-next-path/docs/03-state-machine.md`
- `codex/selective-next-path/docs/04-test-matrix.md`
- `codex/selective-next-path/docs/05-output-schema.md`
- `codex/selective-next-path/docs/06-repository-mapping.md`
- `codex/selective-next-path/docs/07-non-goals.md`

First inspect the existing mixed-tree, key-roll, object-generation, result-I/O, and test code. Then produce a concise implementation plan for Phase 1 only. The plan must identify:

1. existing code to reuse;
2. new or modified files;
3. state types and transition guards;
4. JSON schemas and generated outputs;
5. focused tests;
6. Makefile commands;
7. risks and explicit non-goals.

Do not implement all phases in one task. Do not modify code until the plan is internally consistent.

After the plan is approved, implement Phase 1 as a deterministic, protocol-neutral Python model. The minimum result is:

- a valid pre-accepted Next TA;
- a prebuilt Next RIR/NIR;
- no prebuilt Hosted child;
- simulated Current Suite compromise;
- successful creation and activation of a Hosted Next CA under the prebuilt Next parent;
- rejection of Current-signed Next-key introduction after compromise;
- rejection of an unprepared Delegated CA after compromise;
- no Current fallback after activation;
- deterministic JSON results and Markdown report;
- unit tests for all guards and stable failure reason codes.

Use the repository's existing conventions. Keep generated private material and raw work below `local/`. The Phase 1 target must run without network access or optional PQC dependencies.

At completion, report:

- files changed;
- commands run;
- tests and results;
- output paths;
- unsupported items;
- any deviation from the design documents.
