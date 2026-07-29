# AGENTS.md — Selective Next Path Experiment

## Repository purpose

This repository is an experimental harness for post-quantum signature migration in RPKI. It is not production software.

## Required behavior

- Preserve the repository's existing public/private boundary.
- Put private keys, external source checkouts, build trees, raw operational inputs, and scratch notes below ignored `local/`.
- Commit only reproducible code, synthetic fixtures, sanitized measurements, tests, and explicit limitations.
- Do not implement cryptographic algorithms, RRDP, rsync, or a production validator.
- Reuse the existing OpenSSL/provider, Krill, Routinator/rpki-rs, and rpki-client integration paths.
- Python code requires Python 3.11 or later.
- Use the existing `src/pqc_rpki_lab`, `tools`, `tests`, `testdata`, and `results` layout.
- All public outputs must include `EXPERIMENTAL / NOT FOR PRODUCTION`.
- Network access is forbidden in normal targets. It is allowed only in explicit bootstrap/install targets with `--allow-network`.
- Do not silently modify existing published result files. Add new outputs under `results/selective-next-path/`.
- Do not make standards claims that are not demonstrated by code or cited specifications.
- CCR is optional diagnostic material and must not be a protocol dependency.

## Research model

The implementation must distinguish:

- Current Suite and Next Suite.
- Current Suite states: secure, compromised, retired.
- CA operator roles: trust anchor, RIR/NIR, hosted operator, delegated operator.
- Logical CAs from independently operated CA systems.
- Prebuilt Next CAs from on-demand Hosted CAs.
- Staging from activation and retirement.
- Publication of Current objects from trust in Current objects.

The following security rules are mandatory:

1. A Next Trust Anchor can become accepted only before Current Suite compromise.
2. After Current Suite compromise, a new Next CA key cannot be introduced solely by a Current-Suite signature.
3. A Hosted CA may be created after compromise only under a valid prebuilt Next parent controlled by the authoritative Hosted operator.
4. An unprepared Delegated CA cannot migrate after compromise unless a separately modeled safe out-of-band enrollment exists.
5. Activation requires a valid Next path and semantic equivalence of the scoped outputs.
6. After activation, the RP must not fall back to Current.
7. Replayed or older transition state must not reverse activation or retirement.

## Development workflow

- Inspect existing code before writing replacements.
- Prefer small modules and deterministic JSON fixtures.
- Add unit tests for every transition guard and failure reason.
- Use dataclasses and enums where they improve clarity.
- Keep schemas versioned.
- Produce machine-readable JSON first, then generate Markdown views.
- Run `make test` and the new focused targets before finishing.
- Report commands run, files changed, limitations, and any unsupported dependency.
