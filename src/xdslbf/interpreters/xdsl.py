"""Interpreter using xDSL infrastructure for the BrainF language."""

from dataclasses import dataclass, field

from xdsl.dialects.builtin import ModuleOp
from xdsl.interpreter import (
    Interpreter,
    InterpreterFunctions,
    PythonValues,
    ReturnedValues,
    impl,
    impl_terminator,
    register_impls,
)

from xdslbf.dialects import bf
from xdslbf.interpreters.state import BfState, PointerOutOfBoundsError


@register_impls
class BfFunctions(InterpreterFunctions):
    """Interpreter implementations for the BrainF dialect."""

    @staticmethod
    def set_state(interpreter: Interpreter, state: BfState) -> None:
        """Set the initial BrainF mutable state."""
        interpreter.set_data(BfFunctions, "bf_state", state)

    @staticmethod
    def get_state(interpreter: Interpreter) -> BfState:
        """Get the initial BrainF mutable state."""
        return interpreter.get_data(BfFunctions, "bf_state", BfState)

    @impl(bf.IncOp)
    def run_inc(
        self, interpreter: Interpreter, _op: bf.IncOp, args: PythonValues
    ) -> PythonValues:
        """Interpret the increment operation in BrainF."""
        state = BfFunctions.get_state(interpreter)
        state.memory[state.pointer] += 1
        return args

    @impl(bf.DecOp)
    def run_dec(
        self, interpreter: Interpreter, _op: bf.DecOp, args: PythonValues
    ) -> PythonValues:
        """Interpret the decrement operation in BrainF."""
        state = BfFunctions.get_state(interpreter)
        state.memory[state.pointer] -= 1
        return args

    @impl(bf.LshftOp)
    def run_lshft(
        self, interpreter: Interpreter, _op: bf.LshftOp, args: PythonValues
    ) -> PythonValues:
        """Interpret the left shift operation in BrainF."""
        state = BfFunctions.get_state(interpreter)
        state.pointer -= 1
        if state.pointer < 0:
            raise PointerOutOfBoundsError(f"Pointer value {state.pointer} < 0")
        return args

    @impl(bf.RshftOp)
    def run_rshft(
        self, interpreter: Interpreter, _op: bf.RshftOp, args: PythonValues
    ) -> PythonValues:
        """Interpret the right shift operation in BrainF."""
        state = BfFunctions.get_state(interpreter)
        state.pointer += 1
        if state.pointer > len(state.memory):
            raise PointerOutOfBoundsError(
                f"Pointer value {state.pointer} < {len(state.memory)}"
            )
        return args

    @impl(bf.LoopOp)
    def run_loop(
        self, interpreter: Interpreter, op: bf.LoopOp, args: PythonValues
    ) -> PythonValues:
        """Interpret the loop operation in BrainF."""
        state = BfFunctions.get_state(interpreter)
        while state.memory[state.pointer]:
            assert len(op.regions) > 0
            args = interpreter.run_ssacfg_region(op.regions[0], args)
        return args

    @impl_terminator(bf.RetOp)
    def run_ret(
        self, _interpreter: Interpreter, _op: bf.RetOp, args: PythonValues
    ) -> PythonValues:
        """Interpret the return operation in BrainF."""
        return ReturnedValues(args), ()

    @impl(bf.InOp)
    def run_in(
        self, interpreter: Interpreter, _op: bf.InOp, args: PythonValues
    ) -> PythonValues:
        """Interpret the input operation in BrainF."""
        state = BfFunctions.get_state(interpreter)
        if state.input_stream is None:
            state.memory[state.pointer] = ord(input("> ")[0])
        else:
            state.memory[state.pointer] = ord(state.input_stream.read(1))
        return args

    @impl(bf.OutOp)
    def run_out(
        self, interpreter: Interpreter, _op: bf.OutOp, args: PythonValues
    ) -> PythonValues:
        """Interpret the output operation in BrainF."""
        state = BfFunctions.get_state(interpreter)
        if state.output_stream is None:
            print(chr(state.memory[state.pointer]), end="")
        else:
            state.output_stream.write(chr(state.memory[state.pointer]))
        return args


@dataclass
class BrainFInterpreter:
    """Interpreter for the BrainF language."""

    state: BfState = field(default_factory=BfState)

    def interpret(self, program: ModuleOp) -> None:
        """Interpret a BrainF program."""
        interpreter = Interpreter(program)
        interpreter.register_implementations(BfFunctions())
        BfFunctions.set_state(interpreter, self.state)

        interpreter.run_ssacfg_region(program.body, ())

        if (out := self.state.output_stream) is not None:
            print(out)
        else:
            print()
