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

from dataclasses import dataclass, field

from xdsl.dialects.builtin import ModuleOp

from xdslbf.dialects import bf


@dataclass
class BrainFInterpreter:
    """Interpreter for the BrainF language."""

    pointer: int = 0
    memory: dict[int, int] = field(default_factory=lambda: {0: 0})

    def interpret(self, program: ModuleOp, debug: bool = True) -> None:  # noqa: C901, PLR0912
        """Interpret a BrainF program."""
        if (block := program.body.first_block) is None:
            return
        current_instr = block.first_op

        while current_instr:
            if debug:
                print(
                    f"{current_instr.name} @ {self.pointer} : {self.memory.get(self.pointer, 0)}",
                    end="",
                )

            match type(current_instr):
                case bf.IncOp:
                    if self.pointer not in self.memory:
                        self.memory[self.pointer] = 1
                    else:
                        self.memory[self.pointer] += 1
                    current_instr = current_instr.next_op
                case bf.DecOp:
                    if self.pointer not in self.memory:
                        self.memory[self.pointer] = -1
                    else:
                        self.memory[self.pointer] -= 1
                    current_instr = current_instr.next_op
                case bf.LshftOp:
                    self.pointer -= 1
                    current_instr = current_instr.next_op
                case bf.RshftOp:
                    self.pointer += 1
                    current_instr = current_instr.next_op
                case bf.OutOp:
                    print(chr(self.memory.get(self.pointer, 0)))
                    current_instr = current_instr.next_op
                case bf.InOp:
                    self.memory[self.pointer] = ord(input("> ")[0])
                    current_instr = current_instr.next_op
                case _:
                    raise RuntimeError(f"Unsupported instruction {current_instr}")

            if debug:
                print(f" -> {self.memory.get(self.pointer, 0)}")
