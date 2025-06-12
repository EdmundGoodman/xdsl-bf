"""Compiler for the BrainF language."""

from pathlib import Path

from xdsl.context import Context
from xdsl.dialects import (
    arith,
    scf,
)
from xdsl.dialects.builtin import Builtin, ModuleOp

from xdslbf.dialects import bf
from xdslbf.frontend.parser import BrainFParser


def get_context() -> Context:
    """Get a context with the dialects required to lower BrainF."""
    ctx = Context()
    ctx.load_dialect(arith.Arith)
    ctx.load_dialect(scf.Scf)
    ctx.load_dialect(Builtin)
    ctx.load_dialect(bf.BrainF)

    return ctx


def parse_brainf(program: str, _ctx: Context | None = None) -> ModuleOp:
    """Parse a BrainF program."""
    return BrainFParser(Path("in_memory"), program).parse()


if __name__ == "__main__":
    code = ",[>++<-]."
    module = parse_brainf(code)
    print(module)
