PYTHON ?= python

.PHONY: lint test test-quick test-full smoke ci

lint:
	$(PYTHON) -m ruff check . --select E9,F63,F7,F82
	$(PYTHON) scripts/check_syntax.py

test:
	$(PYTHON) scripts/test_all.py --mode quick

test-quick:
	$(PYTHON) scripts/test_all.py --mode quick

test-full:
	$(PYTHON) scripts/test_all.py --mode full

smoke:
	$(PYTHON) -m pytest -q tests/test_smoke_doctor_and_run.py::test_smoke_doctor_and_run tests/test_build_mvp.py::test_smoke_build_mvp_repo

ci: test
