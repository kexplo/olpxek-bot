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
	poetry run flake8 olpxek_bot --count --show-source --statistics

format: poetry.lock
	poetry run black $(CODE)

build: poetry.lock
	poetry build
