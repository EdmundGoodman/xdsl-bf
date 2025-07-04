#!/usr/bin/env python3
"""Compiler for the BrainF language."""

from pathlib import Path

from xdsl.context import Context
from xdsl.dialects import arith, func, memref, scf
from xdsl.dialects.builtin import Builtin, ModuleOp

from xdslbf.dialects import bf, bfe
from xdslbf.frontend import BrainFParser
from xdslbf.transforms.lower_bf_bfe import LowerBfToBfePass
from xdslbf.transforms.lower_bf_builtin import LowerBfToBuiltinPass

# from xdslbf.transforms.optimise_bfe import OptimiseBfePass


def get_context() -> Context:
    """Get a context with the dialects required to lower BrainF."""
    ctx = Context()
    ctx.load_dialect(arith.Arith)
    ctx.load_dialect(scf.Scf)
    ctx.load_dialect(memref.MemRef)
    ctx.load_dialect(func.Func)
    ctx.load_dialect(Builtin)
    ctx.load_dialect(bf.BrainF)
    ctx.load_dialect(bfe.BrainFExtended)
    return ctx


def parse_brainf(program: str) -> ModuleOp:
    """Parse a BrainF program."""
    return BrainFParser(Path("in_memory"), program).parse()


def lower_bf_builtin(program: str, ctx: Context) -> ModuleOp:
    """Parse a BrainF program and lower it to valid MLIR IR."""
    module = parse_brainf(program)
    LowerBfToBuiltinPass().apply(ctx, module)
    return module


def lower_bf_bfe(program: str, ctx: Context) -> ModuleOp:
    """Parse a BrainF program and lower it to a better custom IR."""
    module = parse_brainf(program)
    LowerBfToBfePass().apply(ctx, module)
    # OptimiseBfePass().apply(ctx, module)
    return module


def get_bf_from_file(name: str) -> str:
    """Get BrainF source code from a file relative to the project root."""
    file = Path(__file__).parent.parent.parent / name
    return file.read_text().strip()


if __name__ == "__main__":
    # code = (
    #     ">++++++++[<+++++++++>-]<.>++++[<+++++++>-]<+.+++++++..+++.>>++++++"
    #     "[<+++++++>-]<++.------------.>++++++[<+++++++++>-]"
    #     "<+.<.+++.------.--------.>>>++++[<++++++++>-]<+."
    # )
    # code = "++>+" # "+++>+<-[--]+"  # <-"
    code = get_bf_from_file("tests/examples/hanoi.bf")

    COMPILE = True
    if COMPILE:
        module = lower_bf_bfe(code, ctx=get_context())
        # module = lower_bf_builtin(code, ctx=get_context())
    else:
        module = parse_brainf(code)
        # from xdslbf.interpreters.bf import BrainFInterpreter
        # BrainFInterpreter().interpret(module)
    print(module)
