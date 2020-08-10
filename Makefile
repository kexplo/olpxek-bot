.PHONY: init test lint format build

CODE = run.py

init:
	poetry install

test:
	poetry run pytest

lint:
	poetry run black --line-length=79 --check $(CODE)

format:
	poetry run black --line-length=79 $(CODE)

build:
	dephell deps convert
