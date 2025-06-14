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

.PHONY: run
run: .venv/
	uv run jacks-menu

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


.PHONY: executable
executable:
	mkdir -p tmp &&\
		python3 src/xdslbf/compiler.py > tmp/out.mlir && cd tmp &&\
		mlir-opt out.mlir --convert-arith-to-llvm --convert-scf-to-cf --convert-cf-to-llvm --convert-func-to-llvm --finalize-memref-to-llvm --reconcile-unrealized-casts -o outllvm.mlir &&\
		mlir-translate --mlir-to-llvmir outllvm.mlir -o out.ll &&\
		clang out.ll -o executable &&\
		./executable
