.PHONY: install install-dev test format lint type-check clean build publish

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

format:
	black tela tests examples
	ruff check --fix tela tests

lint:
	ruff check tela tests
	black --check tela tests

type-check:
	mypy tela

clean:
	rm -rf build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov

build: clean
	python -m build

publish: build
	python -m twine upload dist/*

all: format lint type-check test