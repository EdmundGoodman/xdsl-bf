"""Compiler for the BrainF language."""

from xdsl.context import Context
from xdsl.dialects import (
    arith,
    scf,
)
from xdsl.dialects.builtin import Builtin, ModuleOp

from xdslbf.dialects import bf


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
    print(program)
    # mlir_gen = IRGen()
    # module_ast = ToyParser(Path("in_memory"), program).parseModule()
    # module_op = mlir_gen.ir_gen_module(module_ast)
    # return module_op
    raise NotImplementedError


if __name__ == "__main__":
    code = "++++"
    parse_brainf(code)
