.ONESHELL:
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all

# TODO: Document the fetch step and data layout in README.md
VERBOSE ?= 0
export VERBOSE

FPLCACHE_COMMIT ?=
export FPLCACHE_COMMIT

all: setup fetch run

setup:
	command -v uv >/dev/null 2>&1 || { echo "Error: 'uv' is not installed. See https://docs.astral.sh/uv/"; exit 1; }
	uv sync

fetch:
	bash scripts/fetch_fplcache.sh

run:
	uv run uvicorn app.main:app --reload

test:
	PYTHONPATH=. uv run pytest -q

check:
	uv run ruff check .
	uv run ruff format --check .
