"""Dialect for BrainF's instruction set.

From [Wikipedia](https://en.wikipedia.org/wiki/Brainfuck#Language_design):

- > = Increment the data pointer by one (to point to the next cell to the
  right).
- < = Decrement the data pointer by one (to point to the next cell to the left).
- + = Increment the byte at the data pointer by one.
- - = Decrement the byte at the data pointer by one.
- [ = If the byte at the data pointer is zero, then instead of moving the
  instruction pointer forward to the next command, jump it forward to the
  command after the matching ] command.
- ] = If the byte at the data pointer is nonzero, then instead of moving the
  instruction pointer forward to the next command, jump it back to the command
  after the matching [ command.
- . = Output the byte at the data pointer.
- , = Accept one byte of input, storing its value in the byte at the data
  pointer.
"""

import abc

from xdsl.ir import Dialect
from xdsl.irdl import (
    IRDLOperation,
    irdl_op_definition,
    region_def,
    traits_def,
)
from xdsl.traits import MemoryReadEffect, MemoryWriteEffect


class BrainFOperation(IRDLOperation, abc.ABC):
    """An operation in the BrainF language."""


@irdl_op_definition
class IncOp(BrainFOperation):
    """Increment operation `+`.

    Increment the byte at the data pointer by one.
    """

    name = "bf.inc"

    traits = traits_def(MemoryWriteEffect())


@irdl_op_definition
class DecOp(BrainFOperation):
    """Decrement operation `-`.

    Decrement the byte at the data pointer by one.
    """

    name = "bf.dec"
    traits = traits_def(MemoryWriteEffect())


@irdl_op_definition
class LshftOp(BrainFOperation):
    """Left shift operation `<`.

    Increment the data pointer by one (to point to the next cell to the right).
    """

    name = "bf.lshft"
    traits = traits_def(MemoryWriteEffect())


@irdl_op_definition
class RshftOp(BrainFOperation):
    """Right shift operation `>`.

    Decrement the data pointer by one (to point to the next cell to the left).
    """

    name = "bf.rshft"
    traits = traits_def(MemoryWriteEffect())


@irdl_op_definition
class LoopOp(BrainFOperation):
    """Loop start operation `[`.

    If the byte at the data pointer is zero, then instead of moving the
    instruction pointer forward to the next command, jump it forward to the
    command after the matching ] command.
    """

    name = "bf.loop"

    body = region_def()
    traits = traits_def(MemoryReadEffect())


@irdl_op_definition
class RetOp(BrainFOperation):
    """Loop return operation `]`.

    If the byte at the data pointer is nonzero, then instead of moving the
    instruction pointer forward to the next command, jump it back to the command
    after the matching [ command.
    """

    name = "bf.ret"
    traits = traits_def(MemoryReadEffect())


@irdl_op_definition
class OutOp(BrainFOperation):
    """Output operation `<`.

    Output the byte at the data pointer.
    """

    name = "bf.out"
    traits = traits_def(MemoryReadEffect())


@irdl_op_definition
class InOp(BrainFOperation):
    """Input operation `>`.

    Accept one byte of input, storing its value in the byte at the data pointer.
    """

    name = "bf.in"
    traits = traits_def(MemoryWriteEffect())


BrainF = Dialect(
    "bf",
    [
        IncOp,
        DecOp,
        LshftOp,
        RshftOp,
        LoopOp,
        RetOp,
        OutOp,
        InOp,
    ],
    [],
)
