"""Unit tests for the bfe dialect."""

from xdsl.builder import ImplicitBuilder
from xdsl.dialects import arith
from xdsl.dialects.builtin import IndexType, ModuleOp, i32

from xdslbf.dialects import bfe


def test_bf_builder() -> None:
    """Test building and printing all operations in the bf dialect."""
    module = ModuleOp([])
    with ImplicitBuilder(module.body):
        pointer_init = arith.ConstantOp.from_int_and_width(0, IndexType())

        mem_op_1 = bfe.MemoryOp(
            pointer=pointer_init,
        )
        with ImplicitBuilder(mem_op_1.body):
            data = bfe.LoadOp(2)
            const_1 = arith.ConstantOp.from_int_and_width(1, i32)
            new_data = arith.AddiOp(data, const_1)
            bfe.StoreOp(new_data, 2)
            bfe.MoveOp(mem_op_1.operands[0])

        while_op_1 = bfe.WhileOp(pointer=mem_op_1)
        with ImplicitBuilder(while_op_1.body):
            mem_op_2 = bfe.MemoryOp(
                pointer=while_op_1.operands[0],
            )
            with ImplicitBuilder(mem_op_2.body):
                bfe.MoveOp(mem_op_2.operands[0])
            bfe.MoveOp(while_op_1.operands[0])

    expected = """\
builtin.module {
  %0 = arith.constant 0 : index
  %1 = "bfe.mem"(%0) ({
    %2 = bfe.load 2 : i32
    %3 = arith.constant 1 : i32
    %4 = arith.addi %2, %3 : i32
    bfe.store %4 2
    bfe.move %0 : index
  }) : (index) -> index
  %5 = "bfe.while"(%1) ({
    %6 = "bfe.mem"(%1) ({
      bfe.move %1 : index
    }) : (index) -> index
    bfe.move %1 : index
  }) : (index) -> index
}"""
    assert str(module) == expected
