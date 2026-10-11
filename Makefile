# Analysis of a randomised e-mail campaign experiment. `make help` lists targets.

COMPOSE := docker compose
RUN := $(COMPOSE) run --rm analysis

# Git Bash on Windows rewrites container paths; this switches that off.
export MSYS_NO_PATHCONV := 1

.PHONY: help build data run synthetic-check smoke test lint

help:
	@echo "make data     download the Hillstrom e-mail experiment into data/"
	@echo "make run      analyse it -> evidence/hillstrom/ (results.json, RESULTS.md, plots)"
	@echo "make synthetic-check  same pipeline on synthetic data with planted effects"
	@echo "              -> evidence/synthetic_check/"
	@echo "make smoke    the synthetic run, output to /tmp only (used by CI)"
	@echo "make test     run the tests"
	@echo "make lint     ruff lint + format check (needs ruff installed)"

build:
	$(COMPOSE) build analysis

data:
	@sh scripts/fetch_data.sh

run: build data
	$(RUN) python scripts/run_analysis.py --data data/hillstrom.csv --out evidence/hillstrom
	$(RUN) python scripts/report.py evidence/hillstrom

# Does the pipeline recover effects that are known because they were planted?
# Kept in its own folder, and labelled synthetic in every file it writes.
synthetic-check: build
	$(RUN) python scripts/run_analysis.py --synthetic --out evidence/synthetic_check
	$(RUN) python scripts/report.py evidence/synthetic_check

# Output goes to /tmp inside the container, so nothing is written to evidence/.
smoke: build
	$(RUN) sh -c "python scripts/run_analysis.py --synthetic --out /tmp/smoke && python scripts/report.py /tmp/smoke && cat /tmp/smoke/RESULTS.md"

test: build
	$(RUN) python -m pytest -p no:cacheprovider

lint:
	ruff check .
	ruff format --check .
