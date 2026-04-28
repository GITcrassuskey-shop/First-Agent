.PHONY: install lint format typecheck test check run

install:
	python -m pip install --upgrade pip
	python -m pip install -e ".[dev]"
	pre-commit install

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

typecheck:
	mypy

test:
	pytest

check: lint typecheck test

run:
	fa --help
