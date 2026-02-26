PYTHON ?= python

.PHONY: lint test test-quick test-full smoke ci coverage security

lint:
	$(PYTHON) -m ruff check . --select E9,F63,F7,F82
	$(PYTHON) scripts/check_syntax.py

test:
	$(PYTHON) run_tests.py --type all

test-quick:
	$(PYTHON) run_tests.py --type unit

test-full:
	$(PYTHON) run_tests.py --type all

test-integration:
	$(PYTHON) run_tests.py --type integration

test-smoke:
	$(PYTHON) run_tests.py --type smoke

coverage:
	$(PYTHON) run_tests.py --type all --check-only

coverage-html:
	$(PYTHON) run_tests.py --type all
	@echo "Coverage report generated in htmlcov/index.html"

security:
	$(PYTHON) -m pip install bandit safety
	bandit -r app/
	safety check

ci: lint test-quick security

quality: lint test-full security

benchmark:
	$(PYTHON) -m pytest tests/ -k "benchmark" --benchmark-only

clean:
	$(PYTHON) -m pytest --cache-clear
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/

install-test:
	$(PYTHON) -m pip install -r requirements-test.txt
