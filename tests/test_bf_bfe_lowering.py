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
  %1 = "bfe.mem"(%0) <{move = 0 : index}> ({
    %2 = bfe.in : i32
    bfe.store %2 + 0
  }) : (index) -> index
  %3 = "bfe.mem"(%1) <{move = 1 : index}> ({
  ^0:
  }) : (index) -> index
  %4 = "bfe.mem"(%3) <{move = 0 : index}> ({
    %5 = bfe.load + 0 : i32
    %6 = arith.constant 1 : i32
    %7 = arith.addi %5, %6 : i32
    bfe.store %7 + 0
  }) : (index) -> index
  %8 = "bfe.mem"(%4) <{move = 0 : index}> ({
    %9 = bfe.load + 0 : i32
    %10 = arith.constant 1 : i32
    %11 = arith.addi %9, %10 : i32
    bfe.store %11 + 0
  }) : (index) -> index
  %12 = "bfe.mem"(%8) <{move = -1 : index}> ({
  ^1:
  }) : (index) -> index
  %13 = "bfe.mem"(%12) <{move = 0 : index}> ({
    %14 = bfe.load + 0 : i32
    %15 = arith.constant 1 : i32
    %16 = arith.subi %14, %15 : i32
    bfe.store %16 + 0
  }) : (index) -> index
  %17 = "bfe.mem"(%13) <{move = 0 : index}> ({
    %18 = bfe.load + 0 : i32
    bfe.out %18
  }) : (index) -> index
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
  %1 = "bfe.mem"(%0) <{move = 0 : index}> ({
    %2 = bfe.in : i32
    bfe.store %2 + 0
  }) : (index) -> index
  %3 = "bfe.while"(%1) ({
    %4 = "bfe.mem"(%1) <{move = 1 : index}> ({
    ^0:
    }) : (index) -> index
    %5 = "bfe.mem"(%4) <{move = 0 : index}> ({
      %6 = bfe.load + 0 : i32
      %7 = arith.constant 1 : i32
      %8 = arith.addi %6, %7 : i32
      bfe.store %8 + 0
    }) : (index) -> index
    %9 = "bfe.mem"(%5) <{move = 0 : index}> ({
      %10 = bfe.load + 0 : i32
      %11 = arith.constant 1 : i32
      %12 = arith.addi %10, %11 : i32
      bfe.store %12 + 0
    }) : (index) -> index
    %13 = "bfe.mem"(%9) <{move = -1 : index}> ({
    ^1:
    }) : (index) -> index
    %14 = "bfe.mem"(%13) <{move = 0 : index}> ({
      %15 = bfe.load + 0 : i32
      %16 = arith.constant 1 : i32
      %17 = arith.subi %15, %16 : i32
      bfe.store %17 + 0
    }) : (index) -> index
    bfe.continue %14
  }) : (index) -> index
  %18 = "bfe.mem"(%3) <{move = 0 : index}> ({
    %19 = bfe.load + 0 : i32
    bfe.out %19
  }) : (index) -> index
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
      %3 = bfe.load + 0 : i32
      %4 = arith.constant 1 : i32
      %5 = arith.subi %3, %4 : i32
      bfe.store %5 + 0
    }) : (index) -> index
    %6 = "bfe.while"(%2) ({
      %7 = "bfe.mem"(%2) <{move = 0 : index}> ({
        %8 = bfe.load + 0 : i32
        %9 = arith.constant 1 : i32
        %10 = arith.subi %8, %9 : i32
        bfe.store %10 + 0
      }) : (index) -> index
      bfe.continue %7
    }) : (index) -> index
    %11 = "bfe.while"(%6) ({
      %12 = "bfe.mem"(%6) <{move = 0 : index}> ({
        %13 = bfe.load + 0 : i32
        %14 = arith.constant 1 : i32
        %15 = arith.subi %13, %14 : i32
        bfe.store %15 + 0
      }) : (index) -> index
      bfe.continue %12
    }) : (index) -> index
    bfe.continue %11
  }) : (index) -> index
}"""
    assert str(module) == expected
