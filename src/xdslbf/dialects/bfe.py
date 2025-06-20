"""Dialect for a representation of BrainF amenable to rewriting optimisations.

We use the operands of each basic blocks to capture the memory pointer offset,
as opposed to storing it directly in memory. This then allows us to simply merge
memory operations within the same basic block, and reveals helpful information
about loop invariants which can be optimised.
"""

import abc
from collections.abc import Sequence
from typing import Any

from xdsl.dialects.builtin import I32, IndexType, IndexTypeConstr, IntegerAttr, i32
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
    move = prop_def(IntegerAttr.constr(type=IndexTypeConstr))
    end_pointer = result_def(IndexType())
    body = region_def()

    def __init__(
        self,
        pointer: Operation | SSAValue,
        *,
        move: int = 0,
        regions: Sequence[Region] | None = None,
        properties: dict[str, Attribute | None] | None = None,
        result_types: tuple[IndexType] = (IndexType(),),
        **kwargs: Any,
    ):
        """Default to a single empty region."""
        if regions is None:
            regions = [Region([Block()])]
        if properties is None:
            properties = {}
        properties |= {"move": IntegerAttr(move, IndexType())}
        super().__init__(
            operands=(pointer,),
            result_types=result_types,
            regions=regions,
            properties=properties,
            **kwargs,
        )


@irdl_op_definition
class MemoryOp(BrainFExtendedBlock):
    """Changes to the memory tape at a pointer offset."""

    name = "bfe.mem"

    traits = traits_def(
        RecursiveMemoryEffect(), NoTerminator(), SameOperandsAndResultType()
    )


@irdl_op_definition
class WhileOp(BrainFExtendedBlock):
    """Unbounded iteration whilst the entry memory value is non-zero."""

    name = "bfe.while"

    traits = traits_def(
        RecursiveMemoryEffect(), NoTerminator(), SameOperandsAndResultType()
    )


@irdl_op_definition
class LoadOp(IRDLOperation):
    """Load memory from the tape at a specified offset."""

    name = "bfe.load"

    offset = prop_def(IntegerAttr.constr(type=IndexTypeConstr))
    data = result_def(i32)
    traits = traits_def(MemoryReadEffect())

    assembly_format = "attr-dict $offset `:` type($data)"

    def __init__(self, offset: int, result_types: tuple[I32] = (i32,), **kwargs: Any):
        """Specify the data to store."""
        super().__init__(
            result_types=result_types,
            properties={"offset": IntegerAttr(offset, IndexType())},
            **kwargs,
        )


@irdl_op_definition
class StoreOp(IRDLOperation):
    """Store back into memory in the tape at a specified offset."""

    name = "bfe.store"

    offset = prop_def(IntegerAttr.constr(type=IndexTypeConstr))
    data = operand_def(i32)
    traits = traits_def(MemoryWriteEffect())

    assembly_format = "$data attr-dict $offset"

    def __init__(self, data: Operation | SSAValue, offset: int, **kwargs: Any):
        """Specify the data to store."""
        super().__init__(
            operands=[data],
            properties={"offset": IntegerAttr(offset, IndexType())},
            **kwargs,
        )


BrainFExtended = Dialect(
    "bfe",
    [
        MemoryOp,
        WhileOp,
        LoadOp,
        StoreOp,
    ],
    [],
)
