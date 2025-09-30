PYTHON ?= python3

.PHONY: install run test lint fmt

install:
$(PYTHON) -m pip install --upgrade pip
$(PYTHON) -m pip install -e .[dev]

run:
$(PYTHON) -m app.main

test:
$(PYTHON) -m pytest -q

lint:
$(PYTHON) -m ruff check src tests

fmt:
$(PYTHON) -m black src tests
