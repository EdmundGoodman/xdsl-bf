"""Implementations of mutable state for the BrainF interpreters."""

import abc
from dataclasses import dataclass, field
from io import StringIO
from typing import TextIO

from xdsl.dialects.builtin import ModuleOp


class PointerOutOfBoundsError(RuntimeError):
    """Exception to indicate the pointer is outside the memory tape."""


@dataclass
class BfState:
    """A representation of BrainF mutable state."""

    pointer: int = 0
    memory: list[int] = field(default_factory=lambda: [0] * 30_000)
    input_stream: TextIO | None = None
    output_stream: TextIO | None = None


class BaseBrainFInterpreter(abc.ABC):
    """Interpreter for the BrainF language."""

    state: BfState

    @abc.abstractmethod
    def interpret(self, program: ModuleOp) -> None:
        """Interpret a BrainF program."""
        ...

    @property
    def output(self) -> str:
        """Get the string value of the output stream."""
        assert isinstance(self.state.output_stream, StringIO)
        return self.state.output_stream.getvalue()
