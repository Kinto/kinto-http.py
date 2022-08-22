VIRTUALENV = virtualenv --python=python3
VENV := $(shell echo $${VIRTUAL_ENV-.venv})
PYTHON = $(VENV)/bin/python
DEV_STAMP = $(VENV)/.dev_env_installed.stamp
INSTALL_STAMP = $(VENV)/.install.stamp
TEMPDIR := $(shell mktemp -d)

.IGNORE: clean distclean maintainer-clean
.PHONY: all install virtualenv tests tests-once

OBJECTS = .venv .coverage

all: install
install: $(INSTALL_STAMP)
$(INSTALL_STAMP): $(PYTHON) setup.py
	$(VENV)/bin/pip install -U pip
	$(VENV)/bin/pip install -Ue .
	touch $(INSTALL_STAMP)

install-dev: $(INSTALL_STAMP) $(DEV_STAMP)
$(DEV_STAMP): $(PYTHON) dev-requirements.txt
	$(VENV)/bin/pip install -Ur dev-requirements.txt
	touch $(DEV_STAMP)

virtualenv: $(PYTHON)
$(PYTHON):
	$(VIRTUALENV) $(VENV)

need-kinto-running:
	@curl http://localhost:8888/v0/ 2>/dev/null 1>&2 || (echo "Run 'make run-kinto' before starting tests." && exit 1)

run-kinto: install-dev
	$(VENV)/bin/kinto migrate --ini kinto_http/tests/config/kinto.ini
	$(VENV)/bin/kinto start --ini kinto_http/tests/config/kinto.ini

tests-once: install-dev need-kinto-running
	$(VENV)/bin/pytest --cov-report term-missing --cov-fail-under 100 --cov kinto_http

functional: install-dev need-kinto-running
	$(VENV)/bin/pytest -k "test_functional"

tests: install-dev need-kinto-running lint
	$(VENV)/bin/pytest

format: install-dev
	$(VENV)/bin/isort --profile=black --lines-after-imports=2 kinto_http
	$(VENV)/bin/black kinto_http
	$(VENV)/bin/flake8 kinto_http

lint: install-dev
	$(VENV)/bin/therapist run --use-tracked-files kinto_http

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d | xargs rm -fr

distclean: clean
	rm -fr *.egg *.egg-info/ dist/ build/

maintainer-clean: distclean
	rm -fr .venv/ .tox/
