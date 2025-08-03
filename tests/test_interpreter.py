"""Unit tests for the interpreter."""

from io import StringIO
from typing import Any

from xdslbf.compiler import parse_brainf
from xdslbf.interpreters import BfState, BrainFInterpreter
from xdslbf.interpreters.python import BrainFInterpreter as PythonBrainFInterpreter


def test_interpreter_simple_loop() -> None:
    """Test the interpreter runs a simple loop."""
    code = ",+."
    state = BfState(
        input_stream=StringIO("a"),
        output_stream=StringIO(""),
    )
    interpreter = BrainFInterpreter(state)
    interpreter.interpret(parse_brainf(code))
    assert interpreter.output == "b"


def test_native_interpeter_simple_loop() -> None:
    """Test the interpreter runs a simple loop."""
    code = ",+."
    state = BfState(
        input_stream=StringIO("a"),
        output_stream=StringIO(""),
    )
    interpreter = PythonBrainFInterpreter(state)
    interpreter.interpret(parse_brainf(code))
    assert interpreter.output == "b"


def test_interpreter_stdio(capsys: Any, monkeypatch: Any) -> None:
    """Test the interpreter can handle character input and output."""
    monkeypatch.setattr("builtins.input", lambda _: "a")  # pyright: ignore[reportUnknownLambdaType]
    code = ",."
    BrainFInterpreter().interpret(parse_brainf(code))
    captured = capsys.readouterr()
    assert captured.out.strip() == "a"
