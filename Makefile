PYTHON ?= python3
UV ?= uv

.PHONY: install run test lint fmt

install:
	$(UV) pip install --python "$(shell $(PYTHON) -c 'import sys; print(sys.executable)')" -e '.[dev]'

run:
	$(PYTHON) -m app.main

test:
	$(UV) run pytest -q -k integration \
		|| ( $(UV) pip install -r requirements.txt && $(UV) run pytest -q -k integration )

lint:
	$(PYTHON) -m ruff check src tests

fmt:
	$(PYTHON) -m black src tests
