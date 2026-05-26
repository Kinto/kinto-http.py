.PHONY: all
all: install

install:
	uv sync --all-extras

.PHONY: lint
lint: install
	uv run ruff check src tests
	uv run ruff format --check src tests

.PHONY: format
format:
	uv run ruff check --fix src tests
	uv run ruff format src tests

need-kinto-running:
	@curl http://localhost:8888/v0/ 2>/dev/null 1>&2 || (echo "Run 'make run-kinto' before starting tests." && exit 1)

.PHONY: tests
tests: test
tests-once: test
test: install need-kinto-running
	uv run pytest --cov-report term-missing --cov-fail-under 100 --cov kinto_http

.PHONY: functional
functional: install need-kinto-running
	uv run pytest -k "test_functional"

.IGNORE: clean
clean:
	find src/ -name '__pycache__' -type d -exec rm -fr {} \;
	find tests/ -name '__pycache__' -type d -exec rm -fr {} \;
	rm -rf .coverage *.egg-info .pytest_cache .ruff_cache build dist

run-kinto:
	uv run kinto migrate --ini tests/config/kinto.ini
	uv run kinto start --ini tests/config/kinto.ini
