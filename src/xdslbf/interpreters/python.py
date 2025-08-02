"""Interpreter in pure Python for the BrainF language."""

from collections.abc import Callable
from typing import TextIO

from xdsl.dialects.builtin import ModuleOp
from xdsl.ir import Operation

from xdslbf.dialects import bf
from xdslbf.interpreters.state import BfState, PointerOutOfBoundsError


class BrainFInterpreter:
    """Interpreter for the BrainF language."""

    pointer: int
    memory: list[int]
    input_stream: TextIO | None = None
    output_stream: TextIO | None = None

    def __init__(self, state: BfState | None = None) -> None:
        """Instantiate the interpreter."""
        if state is None:
            state = BfState()
        self.state = state

    @property
    def state(self) -> BfState:
        """Get state on the interpreter."""
        return BfState(self.pointer, self.memory, self.input_stream, self.output_stream)

    @state.setter
    def state(self, state: BfState) -> None:
        """Set state on the interpreter."""
        self.pointer = state.pointer
        self.memory = state.memory
        self.input_stream = state.input_stream
        self.output_stream = state.output_stream

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
            raise PointerOutOfBoundsError(f"Pointer value {self.pointer} < 0")
        return current_instr.next_op

    def _rshft(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.rshft` instruction."""
        self.pointer += 1
        if self.pointer > len(self.memory):
            raise PointerOutOfBoundsError(
                f"Pointer value {self.pointer} < {len(self.memory)}"
            )
        return current_instr.next_op

    def _out(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.out` instruction."""
        if self.output_stream is None:
            print(chr(self.memory[self.pointer]), end="")
        else:
            self.output_stream.write(chr(self.state.memory[self.state.pointer]))
        return current_instr.next_op

    def _in(self, current_instr: Operation) -> Operation | None:
        """Interpret the `bf.in` instruction."""
        if self.input_stream is None:
            self.memory[self.pointer] = ord(input("> ")[0])
        else:
            self.memory[self.pointer] = ord(self.input_stream.read(1))
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
            bf.OutOp: self._out,
            bf.InOp: self._in,
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

        if (out := self.output_stream) is not None:
            print(out)
        else:
            print()
