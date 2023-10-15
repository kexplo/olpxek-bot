.PHONY: init test lint format build

CODE = olpxek_bot

poetry.lock:
	$(MAKE) init

init:
	poetry install
	poetry run python -m playwright install

test: poetry.lock
	poetry run pytest -vv

lint: poetry.lock
	poetry run black --check --diff $(CODE)
	poetry run ruff check $(CODE)

format: poetry.lock
	poetry run black $(CODE)

build: poetry.lock
	poetry build
