"""Unit tests for the bf dialect."""

from xdsl.builder import ImplicitBuilder
from xdsl.dialects.builtin import ModuleOp

from xdslbf.dialects import bf


def test_bf_builder() -> None:
    """Test building and printing all operations in the bf dialect."""
    module = ModuleOp([])
    with ImplicitBuilder(module.body):
        bf.InOp()
        bf.IncOp()
        loop = bf.LoopOp()
        with ImplicitBuilder(loop.body):
            bf.RshftOp()
            bf.DecOp()
            bf.DecOp()
            bf.LshftOp()
            bf.RetOp()
        bf.RshftOp()
        bf.OutOp()
    expected = """\
builtin.module {
  "bf.in"() : () -> ()
  "bf.inc"() : () -> ()
  "bf.loop"() ({
    "bf.rshft"() : () -> ()
    "bf.dec"() : () -> ()
    "bf.dec"() : () -> ()
    "bf.lshft"() : () -> ()
    "bf.ret"() : () -> ()
  }) : () -> ()
  "bf.rshft"() : () -> ()
  "bf.out"() : () -> ()
}"""
    assert str(module) == expected
