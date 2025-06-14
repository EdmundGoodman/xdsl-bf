#!/usr/bin/env python3
"""Compiler for the BrainF language."""

from pathlib import Path

from xdsl.context import Context
from xdsl.dialects import arith, llvm, memref, scf
from xdsl.dialects.builtin import Builtin, ModuleOp

from xdslbf.dialects import bf
from xdslbf.frontend.parser import BrainFParser
from xdslbf.rewrites.lower_builtin import LowerBfToBuiltinPass
from xdslbf.rewrites.lower_llvm import LowerBfBuiltinToLlvmExecutablePass

# from xdslbf.emulator.interpreter import BrainFInterpreter


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
    LowerBfBuiltinToLlvmExecutablePass().apply(ctx, module)
    # CanonicalizePass().apply(ctx, module)
    return module


if __name__ == "__main__":
    code = "+++[>++<-]>"  # ",[>++<-[>>++<-<]]."
    # module = parse_brainf(code)
    module = lower_brainf(code, ctx=get_context())
    print(module)
    # BrainFInterpreter().interpret(module)
