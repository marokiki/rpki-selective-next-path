.PHONY: all selective-next-path selective-next-path-test selective-next-path-phase2 selective-next-path-phase2-test selective-next-path-phase3 selective-next-path-phase3-test selective-next-path-phase4 selective-next-path-phase4-test selective-next-path-phase5 selective-next-path-phase5-test selective-next-path-phase6 selective-next-path-phase6-test selective-next-path-phase7 selective-next-path-phase7-test selective-next-path-all-phases test check-reference clean

PYTHON ?= python3

all: selective-next-path test

selective-next-path:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src $(PYTHON) tools/selective_next_path_fixture.py

selective-next-path-test:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. $(PYTHON) -m unittest discover -s tests -v

selective-next-path-phase2:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. $(PYTHON) tools/phase2_cost_model.py

selective-next-path-phase2-test:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. $(PYTHON) -m unittest tests.test_phase2 -v

selective-next-path-phase3:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. $(PYTHON) tools/phase3_real_fixture.py

selective-next-path-phase3-test:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. $(PYTHON) -m unittest tests.test_phase3 -v

selective-next-path-phase4:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. $(PYTHON) tools/phase4_pqc_fixture.py

selective-next-path-phase4-test:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. $(PYTHON) -m unittest tests.test_phase4 -v

selective-next-path-phase5:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. $(PYTHON) tools/phase5_hosted_workflow.py

selective-next-path-phase5-test:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. $(PYTHON) -m unittest tests.test_phase5 -v

selective-next-path-phase6:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. $(PYTHON) tools/phase6_rp_policy.py

selective-next-path-phase6-test:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. $(PYTHON) -m unittest tests.test_phase6 -v

selective-next-path-phase7:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. $(PYTHON) tools/phase7_scale.py

selective-next-path-phase7-test:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. $(PYTHON) -m unittest tests.test_phase7 -v

selective-next-path-all-phases: selective-next-path selective-next-path-phase2 selective-next-path-phase3 selective-next-path-phase4 selective-next-path-phase5 selective-next-path-phase6 selective-next-path-phase7

check-reference:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) tools/check_reference.py

test: selective-next-path-test check-reference

clean:
	rm -rf build dist .pytest_cache htmlcov
	rm -f .coverage
	rm -rf src/*.egg-info
