"""Unit tests for the bfe dialect."""

import pytest
from xdsl.context import Context

from xdslbf.compiler import get_context, parse_brainf
from xdslbf.transforms.lower_bf_bfe import LowerBfToBfePass


@pytest.fixture(name="ctx")
def fixture_context() -> Context:
    """Get the context for the compiler."""
    return get_context()


def test_simple_bfe_lowering(ctx: Context) -> None:
    """Test lowering a parsed program from bf to bfe without loops."""
    code = ",>++<-."
    module = parse_brainf(code)
    LowerBfToBfePass().apply(ctx, module)
    expected = """\
builtin.module {
  %0 = arith.constant 0 : index
  "bf.in"() : () -> ()
  %1 = "bfe.mem"(%0) <{move = 1 : index}> ({
  ^0:
  }) : (index) -> index
  %2 = "bfe.mem"(%1) <{move = 0 : index}> ({
    %3 = bfe.load 0 : i32
    %4 = arith.constant 1 : i32
    %5 = arith.addi %3, %4 : i32
    bfe.store %5 0
  }) : (index) -> index
  %6 = "bfe.mem"(%2) <{move = 0 : index}> ({
    %7 = bfe.load 0 : i32
    %8 = arith.constant 1 : i32
    %9 = arith.addi %7, %8 : i32
    bfe.store %9 0
  }) : (index) -> index
  %10 = "bfe.mem"(%6) <{move = -1 : index}> ({
  ^1:
  }) : (index) -> index
  %11 = "bfe.mem"(%10) <{move = 0 : index}> ({
    %12 = bfe.load 0 : i32
    %13 = arith.constant 1 : i32
    %14 = arith.subi %12, %13 : i32
    bfe.store %14 0
  }) : (index) -> index
  "bf.out"() : () -> ()
}"""
    assert str(module) == expected


def test_valid_bfe_lowering(ctx: Context) -> None:
    """Test lowering a parsed program from bf to bfe exercising all instructions."""
    code = ",[>++<-]."
    module = parse_brainf(code)
    LowerBfToBfePass().apply(ctx, module)
    expected = """\
builtin.module {
  %0 = arith.constant 0 : index
  "bf.in"() : () -> ()
  %1 = "bfe.while"(%0) ({
    %2 = "bfe.mem"(%0) <{move = 1 : index}> ({
    ^0:
    }) : (index) -> index
    %3 = "bfe.mem"(%2) <{move = 0 : index}> ({
      %4 = bfe.load 0 : i32
      %5 = arith.constant 1 : i32
      %6 = arith.addi %4, %5 : i32
      bfe.store %6 0
    }) : (index) -> index
    %7 = "bfe.mem"(%3) <{move = 0 : index}> ({
      %8 = bfe.load 0 : i32
      %9 = arith.constant 1 : i32
      %10 = arith.addi %8, %9 : i32
      bfe.store %10 0
    }) : (index) -> index
    %11 = "bfe.mem"(%7) <{move = -1 : index}> ({
    ^1:
    }) : (index) -> index
    %12 = "bfe.mem"(%11) <{move = 0 : index}> ({
      %13 = bfe.load 0 : i32
      %14 = arith.constant 1 : i32
      %15 = arith.subi %13, %14 : i32
      bfe.store %15 0
    }) : (index) -> index
    bfe.continue %12
  }) : (index) -> index
  "bf.out"() : () -> ()
}"""
    assert str(module) == expected


def test_multiloop_bfe_lowering(ctx: Context) -> None:
    """Test lowering a parsed program from bf to bfe with multiple loops."""
    code = "[-[-][-]]"
    module = parse_brainf(code)
    LowerBfToBfePass().apply(ctx, module)
    expected = """\
builtin.module {
  %0 = arith.constant 0 : index
  %1 = "bfe.while"(%0) ({
    %2 = "bfe.mem"(%0) <{move = 0 : index}> ({
      %3 = bfe.load 0 : i32
      %4 = arith.constant 1 : i32
      %5 = arith.subi %3, %4 : i32
      bfe.store %5 0
    }) : (index) -> index
    %6 = "bfe.while"(%2) ({
      %7 = "bfe.mem"(%2) <{move = 0 : index}> ({
        %8 = bfe.load 0 : i32
        %9 = arith.constant 1 : i32
        %10 = arith.subi %8, %9 : i32
        bfe.store %10 0
      }) : (index) -> index
      bfe.continue %7
    }) : (index) -> index
    %11 = "bfe.while"(%6) ({
      %12 = "bfe.mem"(%6) <{move = 0 : index}> ({
        %13 = bfe.load 0 : i32
        %14 = arith.constant 1 : i32
        %15 = arith.subi %13, %14 : i32
        bfe.store %15 0
      }) : (index) -> index
      bfe.continue %12
    }) : (index) -> index
    bfe.continue %11
  }) : (index) -> index
}"""
    assert str(module) == expected
