# Expected repository integration

Inspect the current repository before implementation. The following paths are expected extension points, not mandatory replacements.

## Existing components to reuse

- `src/pqc_rpki_lab/mixed_tree.py`
- `tools/mixed_tree_fixture.py`
- `tools/key_roll_benchmark.py`
- `tools/generate_rpki_objects.py`
- `tools/composite_e2e.py`
- `tools/run_krill_experimental.sh`
- `tools/routinator_experimental_matrix.py`
- existing JSON and Markdown result helpers
- existing tests and Makefile conventions

## Suggested new paths

```text
src/pqc_rpki_lab/selective_next_path.py
src/pqc_rpki_lab/transition_state.py
src/pqc_rpki_lab/transition_cost.py

tools/selective_next_path_fixture.py
tools/selective_next_path_report.py

tests/test_selective_next_path.py
tests/test_transition_state.py
tests/test_transition_cost.py

testdata/selective-next-path/
results/selective-next-path/
```

Codex may choose fewer modules when a smaller design is clearer.

## Suggested Makefile targets

```make
selective-next-path:
	PYTHONPATH=src python3 tools/selective_next_path_fixture.py

selective-next-path-test:
	PYTHONPATH=src python3 -m unittest \
	  tests.test_selective_next_path \
	  tests.test_transition_state \
	  tests.test_transition_cost -v
```

Add the focused target to `regenerate-reports` only after it is deterministic and does not require network access or optional software.

Do not remove or reinterpret the existing synthetic Mixed-Tree fixture. The new model should either import shared types or clearly distinguish its stronger post-compromise rules.
