.PHONY: server cli test

server:
	@echo "Starting server..."
	@python tinydist/server.py

cli:
	@echo "Building CLI tool..."
	pip install --editable .

test:
	@echo "Running tests..."
	@pytest

sort:
	@isort .

lint:
	@echo "Running linter..."
	@flake8 .
	@isort . --check-only

