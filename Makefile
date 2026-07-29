.PHONY: all selective-next-path selective-next-path-test test check-reference clean

PYTHON ?= python3

all: selective-next-path test

selective-next-path:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src $(PYTHON) tools/selective_next_path_fixture.py

selective-next-path-test:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. $(PYTHON) -m unittest discover -s tests -v

check-reference:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) tools/check_reference.py

test: selective-next-path-test check-reference

clean:
	rm -rf build dist .pytest_cache htmlcov
	rm -f .coverage
	rm -rf src/*.egg-info
