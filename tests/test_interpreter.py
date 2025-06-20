"""Unit tests for the emulator."""

from typing import Any

from xdslbf.compiler import parse_brainf
from xdslbf.interpreters import BrainFInterpreter


def test_emulator_simple_loop() -> None:
    """Test the emulator runs a simple loop."""
    code = ",[>++<-]>."
    interpreter = BrainFInterpreter(input_=[5], output=[])
    interpreter.interpret(parse_brainf(code))
    assert interpreter.output == [10]


def test_emulator_stdio(capsys: Any, monkeypatch: Any) -> None:
    """Test the emulator can handle character input and output."""
    monkeypatch.setattr("builtins.input", lambda _: "a")  # pyright: ignore[reportUnknownLambdaType]
    code = ",."
    BrainFInterpreter().interpret(parse_brainf(code))
    captured = capsys.readouterr()
    assert captured.out.strip() == "a"
