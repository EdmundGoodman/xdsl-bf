"""Interpreter for the BrainF language.

Approach sketch:

```python
from typing import Any

from xdsl.interpreter import (
    Interpreter,
    InterpreterFunctions,
    impl_terminator,
    register_impls,
)

from xdslbf.dialects import bf


@register_impls
class BrainFFunctions(InterpreterFunctions):
    '''Implementations for the operations of the BrainF language.'''

    @impl_terminator(bf.IncOp)
    def run_inc(
        self, interpreter: Interpreter, op: bf.IncOp, args: tuple[Any, ...]
    ) -> tuple[Any, ...]:
        '''Implementation for the increment operation.'''
        raise NotImplementedError
```
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from xdsl.dialects.builtin import ModuleOp
from xdsl.ir import Operation

from xdslbf.dialects import bf


@dataclass
class BrainFInterpreter:
    """Interpreter for the BrainF language."""

    pointer: int = 0
    memory: dict[int, int] = field(default_factory=lambda: {0: 0})

    output: list[int] | None = None
    input_: list[int] | None = None

    def _inc(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.inc` instruction."""
        if self.pointer not in self.memory:
            self.memory[self.pointer] = 1
        else:
            self.memory[self.pointer] += 1
        return current_instr.next_op

    def _dec(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.dec` instruction."""
        if self.pointer not in self.memory:
            self.memory[self.pointer] = -1
        else:
            self.memory[self.pointer] -= 1
        return current_instr.next_op

    def _lshft(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.lshft` instruction."""
        self.pointer -= 1
        return current_instr.next_op

    def _rshft(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.rshft` instruction."""
        self.pointer += 1
        return current_instr.next_op

    def _out(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.out` instruction.

        Alternative ASCII-based implementation:

        ```python
        print(chr(self.memory.get(self.pointer, 0)))
        ```
        """
        print(self.memory.get(self.pointer, 0))
        return current_instr.next_op

    def _out_list(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.out` instruction to a list."""
        assert self.output is not None
        self.output.append(self.memory.get(self.pointer, 0))
        return current_instr.next_op

    def _in(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.in` instruction.

        Alternative ASCII-based implementation:

        ```python
        self.memory[self.pointer] = ord(input("> ")[0])
        ```
        """
        self.memory[self.pointer] = int(input("> "))
        return current_instr.next_op

    def _in_list(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.in` instruction from a list."""
        assert self.input_ is not None
        self.memory[self.pointer] = self.input_.pop(0)
        return current_instr.next_op

    def _loop(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.loop` instruction."""
        if self.memory[self.pointer]:
            # If non-zero, go to the first loop instruction in the region
            loop_regions = current_instr.regions
            assert len(loop_regions) > 0
            loop_block = loop_regions[0].first_block
            assert loop_block is not None
            return loop_block.first_op

        # If zero, jump to the next instruction after the loop region
        return current_instr.next_op

    def _ret(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.ret` instruction."""
        if self.memory[self.pointer]:
            # If non-zero, go to the first loop instruction in the region
            assert current_instr.parent is not None
            return current_instr.parent.first_op

        # If zero, jump to the next instruction after the loop region
        assert current_instr.parent is not None
        assert current_instr.parent.parent is not None
        assert current_instr.parent.parent.parent is not None
        return current_instr.parent.parent.parent.next_op

    def get_operation_implementations(
        self,
    ) -> dict[type[Operation], Callable[[Operation], Operation | None]]:
        """Get the operation implementations."""
        return {
            bf.IncOp: self._inc,
            bf.DecOp: self._dec,
            bf.LshftOp: self._lshft,
            bf.RshftOp: self._rshft,
            bf.OutOp: self._out if self.output is None else self._out_list,
            bf.InOp: self._in if self.input_ is None else self._in_list,
            bf.LoopOp: self._loop,
            bf.RetOp: self._ret,
        }

    def interpret(self, program: ModuleOp) -> None:
        """Interpret a BrainF program."""
        operation_implementations = self.get_operation_implementations()

        if (block := program.body.first_block) is None:
            return
        current_instr: Operation | None = block.first_op

        while current_instr:
            impl = operation_implementations.get(type(current_instr), None)
            if impl is None:
                raise RuntimeError(f"Unsupported instruction {current_instr}")
            current_instr = impl(current_instr)
