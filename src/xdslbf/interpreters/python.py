"""Interpreter for the BrainF language."""

from collections.abc import Callable
from dataclasses import dataclass, field

from xdsl.dialects.builtin import ModuleOp
from xdsl.ir import Operation

from xdslbf.dialects import bf


@dataclass
class BrainFInterpreter:
    """Interpreter for the BrainF language."""

    pointer: int = 0
    memory: list[int] = field(default_factory=lambda: [0] * 30_000)

    output: list[int] | None = None
    input_: list[int] | None = None

    def _inc(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.inc` instruction."""
        self.memory[self.pointer] += 1
        return current_instr.next_op

    def _dec(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.dec` instruction."""
        self.memory[self.pointer] -= 1
        return current_instr.next_op

    def _lshft(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.lshft` instruction."""
        self.pointer -= 1
        if self.pointer < 0:
            raise RuntimeError("Access beyond memory tape!")
        return current_instr.next_op

    def _rshft(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.rshft` instruction."""
        self.pointer += 1
        if self.pointer > len(self.memory):
            raise RuntimeError("Access beyond memory tape!")
        return current_instr.next_op

    def _out(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.out` instruction."""
        print(chr(self.memory[self.pointer]), end="")
        return current_instr.next_op

    def _out_list(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.out` instruction to a list."""
        assert self.output is not None
        self.output.append(self.memory[self.pointer])
        return current_instr.next_op

    def _in(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.in` instruction."""
        self.memory[self.pointer] = ord(input("> ")[0])
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

    def _get_operation_implementations(
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
        operation_implementations = self._get_operation_implementations()

        if (block := program.body.first_block) is None:
            return
        current_instr: Operation | None = block.first_op

        while current_instr:
            impl = operation_implementations.get(type(current_instr), None)
            if impl is None:
                raise RuntimeError(f"Unsupported instruction {current_instr}")
            current_instr = impl(current_instr)
