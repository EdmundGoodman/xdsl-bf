"""Dialect for a representation of BrainF amenable to rewriting optimisations.

We use the operands of each basic blocks to capture the memory pointer offset,
as opposed to storing it directly in memory. This then allows us to simply merge
memory operations within the same basic block, and reveals helpful information
about loop invariants which can be optimised.
"""

import abc
from collections.abc import Sequence
from typing import Any

from xdsl.dialects.builtin import IndexType, IndexTypeConstr, IntegerAttr, i32
from xdsl.ir import Attribute, Block, Dialect, Operation, Region, SSAValue
from xdsl.irdl import (
    IRDLOperation,
    irdl_op_definition,
    operand_def,
    prop_def,
    region_def,
    result_def,
    traits_def,
)
from xdsl.traits import (
    IsTerminator,
    MemoryReadEffect,
    MemoryWriteEffect,
    NoTerminator,
    RecursiveMemoryEffect,
    SameOperandsAndResultType,
)


class BrainFExtendedOperation(IRDLOperation, abc.ABC):
    """An extended IR for the BrainF language."""


class BrainFExtendedBlock(BrainFExtendedOperation):
    """Block in the IR for the BrainF language."""

    start_pointer = operand_def(IndexType())
    end_pointer = result_def(IndexType())
    body = region_def()

    def __init__(
        self,
        pointer: Operation | SSAValue,
        *,
        regions: Sequence[Region] | None = None,
        properties: dict[str, Attribute | None] | None = None,
        **kwargs: Any,
    ):
        """Default to a single empty region."""
        if regions is None:
            regions = [Region([Block()])]
        super().__init__(
            operands=(pointer,),
            result_types=(IndexType(),),
            regions=regions,
            properties=properties,
            **kwargs,
        )


@irdl_op_definition
class MemoryOp(BrainFExtendedBlock):
    """Changes to the memory tape at a pointer offset."""

    name = "bfe.mem"

    move = prop_def(IntegerAttr.constr(type=IndexTypeConstr))
    traits = traits_def(
        RecursiveMemoryEffect(), NoTerminator(), SameOperandsAndResultType()
    )

    def get_move(self) -> int:
        """Get the move offset of the memory block."""
        move = self.properties["move"]
        assert isinstance(move, IntegerAttr)
        return move.value.data

    def __init__(
        self,
        pointer: Operation | SSAValue,
        *,
        move: int = 0,
        regions: Sequence[Region] | None = None,
        **kwargs: Any,
    ):
        """Set the move offset as a property."""
        super().__init__(
            pointer=pointer,
            regions=regions,
            properties={"move": IntegerAttr(move, IndexType())},
            **kwargs,
        )


@irdl_op_definition
class WhileOp(BrainFExtendedBlock):
    """Unbounded iteration whilst the entry memory value is non-zero."""

    name = "bfe.while"

    traits = traits_def(RecursiveMemoryEffect(), SameOperandsAndResultType())


@irdl_op_definition
class ContinueOp(IRDLOperation):
    """Unbounded iteration whilst the entry memory value is non-zero."""

    name = "bfe.continue"
    end_pointer = operand_def(IndexType())

    traits = traits_def(IsTerminator())

    assembly_format = "attr-dict $end_pointer"

    def __init__(
        self,
        pointer: Operation | SSAValue,
        **kwargs: Any,
    ):
        """Construct with the pointer to return with."""
        super().__init__(
            operands=(pointer,),
            **kwargs,
        )


class OffsetOp(IRDLOperation, abc.ABC):
    """An operation with a specified memory offset."""

    offset = prop_def(IntegerAttr.constr(type=IndexTypeConstr))

    def get_offset(self) -> int:
        """Get the offset value of the operation."""
        return self.offset.value.data

    def set_offset(self, offset: int) -> None:
        """Set the offset value of the operation."""
        self.properties["offset"] = IntegerAttr(offset, IndexType())


@irdl_op_definition
class LoadOp(OffsetOp):
    """Load memory from the tape at a specified offset."""

    name = "bfe.load"

    data = result_def(i32)
    traits = traits_def(MemoryReadEffect())

    assembly_format = "attr-dict `+` $offset `:` type($data)"

    def __init__(self, offset: int, **kwargs: Any):
        """Specify the data to store."""
        super().__init__(
            result_types=(i32,),
            properties={"offset": IntegerAttr(offset, IndexType())},
            **kwargs,
        )


@irdl_op_definition
class StoreOp(OffsetOp):
    """Store back into memory in the tape at a specified offset."""

    name = "bfe.store"

    data = operand_def(i32)
    traits = traits_def(MemoryWriteEffect())

    assembly_format = "$data attr-dict `+` $offset"

    def __init__(self, data: Operation | SSAValue, offset: int, **kwargs: Any):
        """Specify the data to store."""
        super().__init__(
            operands=[data],
            properties={"offset": IntegerAttr(offset, IndexType())},
            **kwargs,
        )


@irdl_op_definition
class InOp(IRDLOperation):
    """Load data from the standard input."""

    name = "bfe.in"

    data = result_def(i32)
    traits = traits_def(MemoryWriteEffect())

    assembly_format = "attr-dict `:` type($data)"

    def __init__(self, **kwargs: Any):
        """Specify the result type."""
        super().__init__(
            result_types=(i32,),
            **kwargs,
        )


@irdl_op_definition
class OutOp(IRDLOperation):
    """Output data to the standard output."""

    name = "bfe.out"

    data = operand_def(i32)
    traits = traits_def(MemoryReadEffect())

    assembly_format = "attr-dict $data"

    def __init__(self, data: Operation | SSAValue, **kwargs: Any):
        """Specify the data to store."""
        super().__init__(
            operands=[data],
            **kwargs,
        )


BrainFExtended = Dialect(
    "bfe",
    [
        MemoryOp,
        WhileOp,
        ContinueOp,
        LoadOp,
        StoreOp,
        InOp,
        OutOp,
    ],
    [],
)
