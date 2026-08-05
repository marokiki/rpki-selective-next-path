# Selective Next Path + Mixed-Tree

> EXPERIMENTAL / NOT FOR PRODUCTION

This repository contains a deterministic, protocol-neutral state-machine model for selective post-quantum migration in the Resource Public Key Infrastructure (RPKI).
It models pre-acceptance of a Next Trust Anchor, prebuilt upper certification paths, on-demand Hosted CA creation, CA-scoped activation, and rollback protection after Current Suite compromise.

The accompanying research-design document is available through [GitHub Pages](https://marokiki.github.io/rpki-selective-next-path/).

## Requirements

- Python 3.11 or later
- GNU Make or a compatible implementation

## Run

```sh
make selective-next-path
make selective-next-path-test
make test
```

`make selective-next-path` generates the following deterministic artifacts:

```text
results/selective-next-path/
├── topology.json
├── scenario-results.json
├── cost-model.json
└── report.md
```

The JSON files are the primary machine-readable artifacts.
`report.md` is a generated view of the same data.

## Model

Phase 1 models:

- Current Suite states: `secure`, `compromised`, and `retired`
- Next Trust Anchor states: `absent`, `observed`, and `accepted`
- Trust Anchor, RIR/NIR, Hosted, and Delegated CA roles
- Prebuilt Next paths and on-demand Hosted CAs
- Staging, dual publication, semantic comparison, activation, and retirement
- Per-scope monotonic transition sequences and rollback protection
- No fallback to Current after activation

Semantic comparison is configured per scope.
It compares normalized resource sets, VRPs, ASPAs, and child delegations without requiring byte identity for DER, URIs, SIA, AIA, or validity fields.

## Repository layout

```text
src/selective_next_path/        State machine, semantic comparison, cost model, result I/O
tools/                          Fixture generation and reference-boundary checks
tests/                          Unit tests, including scenarios T01-T20
testdata/selective-next-path/   Public synthetic input
results/selective-next-path/    Deterministic generated results
docs/                           Research design and GitHub Pages source
prompts/                        Work units for later phases
reference/pqc-rpki-lab/         Pinned read-only reference submodule
```

## RPKI lab reference

`reference/pqc-rpki-lab` is a Git submodule pinned to a specific public commit of the reference implementation.
Phase 1 does not import code from this submodule, and `reference/` is excluded from package, build, and test discovery.

Clone the repository and initialize the reference with:

```sh
git clone --recurse-submodules https://github.com/marokiki/rpki-selective-next-path.git
```

Initialize it later with:

```sh
git submodule update --init
make check-reference
```

The reference check requires the pinned detached HEAD and a clean submodule worktree.

## Boundaries

- Private keys, external checkouts, build trees, raw operational inputs, and scratch notes belong under ignored `local/` paths.
- CCR is optional diagnostic material and is not a protocol dependency.
- The Phase 1 cost model reports synthetic counts and coverage, not measured byte sizes, repository behavior, HSM behavior, or timing.
- The results do not establish production interoperability or standards conformance.
