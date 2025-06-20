MAKEFLAGS += --warn-undefined-variables
SHELL := bash

# allow overriding which dependency groups are installed
VENV_GROUPS ?= --group dev --group docs

# set default lit options
LIT_OPTIONS ?= -v --order=smart


.PHONY: install
install: .venv/ pre-commit

.venv/:
	uv sync ${VENV_GROUPS}

.PHONY: pre-commit
pre-commit: .venv/
	uv run pre-commit install

.PHONY: check
check: .venv/
	uv run pre-commit run --all-files

.PHONY: pyright
pyright: .venv/
	uv run pyright $(shell git diff --staged --name-only  -- '*.py')

.PHONY: test
test: pytest filecheck

.PHONY: pytest
pytest: .venv/
	uv run pytest -W error --cov

.PHONY: filecheck
filecheck: .venv/
	uv run lit $(LIT_OPTIONS) tests/filecheck

.PHONY: docs
docs: .venv/
	uv run mkdocs serve
	uv run mkdocs build

.PHONY: clean-caches
clean-caches:
	rm -rf .mypy_cache/ .pytest_cache/ .ruff_cache/ .coverage
	find . -not -path "./.venv/*" | \
		grep -E "(/__pycache__$$|\.pyc$$|\.pyo$$)" | \
		xargs rm -rf

.PHONY: clean
clean: clean-caches
	rm -rf ${VENV_DIR}

# ============================================================================ #

build/out.mlir: .venv/
	mkdir -p build &&\
		python3 src/xdslbf/compiler.py > build/out.mlir

build/lowered.mlir: build/out.mlir
	mlir-opt build/out.mlir \
		--convert-arith-to-llvm \
		--convert-scf-to-cf \
		--convert-cf-to-llvm \
		--convert-func-to-llvm \
		--finalize-memref-to-llvm \
		--reconcile-unrealized-casts \
		-o build/lowered.mlir

build/optimised.mlir: build/lowered.mlir
	mlir-opt build/lowered.mlir \
		--canonicalize \
		--cse \
		--symbol-dce \
		--inline \
		--loop-invariant-code-motion \
		--mem2reg \
		--sroa \
		--sccp \
		--strip-debuginfo \
		-o build/optimised.mlir

build/out.ll: build/optimised.mlir
	mlir-translate --mlir-to-llvmir build/optimised.mlir -o build/out.ll

build/executable: build/out.ll
	clang -O0 build/out.ll -o build/executable

.PHONY: cleanbuild
cleanbuild:
	rm -rf build && mkdir -p build

.PHONY: executable
executable: cleanbuild build/executable
	./build/executable
