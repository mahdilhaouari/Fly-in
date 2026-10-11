PYTHON = uv run python
MAP ?= maps/challenger/01_the_impossible_dream.txt

.PHONY: install run visual debug clean lint lint-strict

install:
	uv sync

run:
	$(PYTHON) main.py $(MAP)

visual:
	$(PYTHON) main.py $(MAP) --visual

debug:
	$(PYTHON) -m pdb main.py $(MAP)

clean:
	rm -rf __pycache__ .mypy_cache

lint:
	uv run flake8 .
	uv run mypy . --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 .
	uv run mypy . --strict