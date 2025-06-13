"""Unit tests for the emulator."""

from typing import Any

from xdslbf.compiler import parse_brainf
from xdslbf.emulator.interpreter import BrainFInterpreter


def test_emulator_simple_loop() -> None:
    """Test the emulator runs a simple loop."""
    code = ",[>++<-]>."
    interpreter = BrainFInterpreter(input_=[5], output=[])
    interpreter.interpret(parse_brainf(code))
    assert interpreter.output == [10]


def test_emulator_simple_loop_stdio(capsys: Any, monkeypatch: Any) -> None:
    """Test the emulator runs a simple loop via stdio."""
    monkeypatch.setattr("builtins.input", lambda _: "5")  # pyright: ignore[reportUnknownLambdaType]
    code = ",[>++<-]>."
    BrainFInterpreter().interpret(parse_brainf(code))
    captured = capsys.readouterr()
    assert captured.out.strip() == "10"
