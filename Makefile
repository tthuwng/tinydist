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
	@isort --profile black --check .

lint:
	@echo "Running linter..."
	@black --check --preview .
	@isort --profile black --check .

