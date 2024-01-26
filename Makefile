VENV := $(shell echo $${VIRTUAL_ENV-.venv})
PYTHON = $(VENV)/bin/python
INSTALL_STAMP = $(VENV)/.install.stamp

.PHONY: all
all: install

install: $(INSTALL_STAMP)
$(INSTALL_STAMP): $(PYTHON) pyproject.toml requirements.txt
	$(VENV)/bin/pip install -U pip
	$(VENV)/bin/pip install -r requirements.txt
	$(VENV)/bin/pip install -e ".[dev]"
	touch $(INSTALL_STAMP)

$(PYTHON):
	python3 -m venv $(VENV)

need-kinto-running:
	@curl http://localhost:8888/v0/ 2>/dev/null 1>&2 || (echo "Run 'make run-kinto' before starting tests." && exit 1)

run-kinto: install
	$(VENV)/bin/kinto migrate --ini kinto_http/tests/config/kinto.ini
	$(VENV)/bin/kinto start --ini kinto_http/tests/config/kinto.ini

.PHONY: tests
test: tests
tests: install need-kinto-running
	$(VENV)/bin/pytest --cov-report term-missing --cov-fail-under 100 --cov kinto_http

.PHONY: functional
functional: install need-kinto-running
	$(VENV)/bin/pytest -k "test_functional"

.PHONY: lint
lint: install
	$(VENV)/bin/ruff check kinto_http/ tests
	$(VENV)/bin/ruff format --check kinto_http/ tests

.PHONY: format
format: install
	$(VENV)/bin/ruff check --fix kinto_http/ tests
	$(VENV)/bin/ruff format kinto_http/ tests

.IGNORE: clean
clean:
	find kinto_http -name '*.pyc' -delete
	find kinto_http -name '__pycache__' -type d -exec rm -fr {} \;
	rm -rf .venv .coverage *.egg-info .pytest_cache .ruff_cache build dist
