"""Implementations of mutable state for the BrainF interpreters."""

from dataclasses import dataclass, field
from typing import TextIO


class PointerOutOfBoundsError(RuntimeError):
    """Exception to indicate the pointer is outside the memory tape."""


@dataclass
class BfState:
    """A representation of BrainF mutable state."""

    pointer: int = 0
    memory: list[int] = field(default_factory=lambda: [0] * 30_000)
    input_stream: TextIO | None = None
    output_stream: TextIO | None = None
