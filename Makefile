MAKEFLAGS += --warn-undefined-variables
SHELL := bash

.PHONY: install
install: .venv/ pre-commit

.venv/:
	uv sync

.PHONY: pre-commit
pre-commit: .venv/
	uv run pre-commit install

.PHONY: check
check: .venv/
	uv run pre-commit run --all-files

.PHONY: test
test: .venv/
	uv run coverage run -m pytest -s &&\
 		uv run coverage report -m

.PHONY: publish
publish:
	uv build
	uv publish

.PHONY: docs
docs: .venv/
	uv run mkdocs build --strict

.PHONY: view_docs
view_docs:
	@open site/index.html

.PHONY: clean
clean:
	rm -rf .mypy_cache/ .pytest_cache/ .ruff_cache/ .coverage
	find . -not -path "./.venv/*" | \
		grep -E "(/__pycache__$$|\.pyc$$|\.pyo$$)" | \
		xargs rm -rf

.PHONY: clobber
clobber: clean
	rm -rf .venv/


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
