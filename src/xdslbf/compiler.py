#!/usr/bin/env python3
"""Compiler for the BrainF language."""

from pathlib import Path

from xdsl.context import Context
from xdsl.dialects import arith, llvm, memref, scf
from xdsl.dialects.builtin import Builtin, ModuleOp

from xdslbf.dialects import bf
from xdslbf.emulator.interpreter import BrainFInterpreter
from xdslbf.frontend.parser import BrainFParser
from xdslbf.rewrites.lower_builtin import LowerBfToBuiltinPass


def get_context() -> Context:
    """Get a context with the dialects required to lower BrainF."""
    ctx = Context()
    ctx.load_dialect(arith.Arith)
    ctx.load_dialect(scf.Scf)
    ctx.load_dialect(memref.MemRef)
    ctx.load_dialect(llvm.LLVM)
    ctx.load_dialect(Builtin)
    ctx.load_dialect(bf.BrainF)
    return ctx


def parse_brainf(program: str) -> ModuleOp:
    """Parse a BrainF program."""
    return BrainFParser(Path("in_memory"), program).parse()


def lower_brainf(program: str, ctx: Context) -> ModuleOp:
    """Parse a BrainF program."""
    module = parse_brainf(program)
    LowerBfToBuiltinPass().apply(ctx, module)
    return module


if __name__ == "__main__":
    code = (
        ">++++++++[<+++++++++>-]<.>++++[<+++++++>-]<+.+++++++..+++.>>++++++"
        "[<+++++++>-]<++.------------.>++++++[<+++++++++>-]"
        "<+.<.+++.------.--------.>>>++++[<++++++++>-]<+."
    )
    module = parse_brainf(code)
    # print(module)

    COMPILE = True
    if COMPILE:
        print(lower_brainf(code, ctx=get_context()))
    else:
        BrainFInterpreter().interpret(module)
