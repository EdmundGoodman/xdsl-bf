#!/usr/bin/env python3
"""Unit tests for the parser."""

from typing import Any

import pytest
from xdsl.utils.exceptions import ParseError

from xdslbf.compiler import parse_brainf
from xdslbf.emulator.interpreter import BrainFInterpreter


def test_simple_parse() -> None:
    """Test the parser with example code without loops."""
    code = ",>++<-."
    parsed = parse_brainf(code)
    expected = """\
builtin.module {
  "bf.in"() : () -> ()
  "bf.rshft"() : () -> ()
  "bf.inc"() : () -> ()
  "bf.inc"() : () -> ()
  "bf.lshft"() : () -> ()
  "bf.dec"() : () -> ()
  "bf.out"() : () -> ()
}"""
    assert str(parsed) == expected


def test_valid_parse() -> None:
    """Test the parser with example code exercising all instructions."""
    code = ",[>++<-]."
    parsed = parse_brainf(code)
    expected = """\
builtin.module {
  "bf.in"() : () -> ()
  "bf.loop"() ({
    "bf.rshft"() : () -> ()
    "bf.inc"() : () -> ()
    "bf.inc"() : () -> ()
    "bf.lshft"() : () -> ()
    "bf.dec"() : () -> ()
    "bf.ret"() : () -> ()
  }) : () -> ()
  "bf.out"() : () -> ()
}"""
    assert str(parsed) == expected


def test_nested_parse() -> None:
    """Test the parser with example code exercising all instructions."""
    code = ",[>++<-[>>++<-<]]."
    parsed = parse_brainf(code)
    expected = """\
builtin.module {
  "bf.in"() : () -> ()
  "bf.loop"() ({
    "bf.rshft"() : () -> ()
    "bf.inc"() : () -> ()
    "bf.inc"() : () -> ()
    "bf.lshft"() : () -> ()
    "bf.dec"() : () -> ()
    "bf.loop"() ({
      "bf.rshft"() : () -> ()
      "bf.rshft"() : () -> ()
      "bf.inc"() : () -> ()
      "bf.inc"() : () -> ()
      "bf.lshft"() : () -> ()
      "bf.dec"() : () -> ()
      "bf.lshft"() : () -> ()
      "bf.ret"() : () -> ()
    }) : () -> ()
    "bf.ret"() : () -> ()
  }) : () -> ()
  "bf.out"() : () -> ()
}"""
    assert str(parsed) == expected


def test_undefined_instructions_parse() -> None:
    """Test the parser rejects invalid characters."""
    code = "abc"
    with pytest.raises(ParseError) as exc:
        parse_brainf(code)
    assert exc.value.msg == "Unexpected character: a"


def test_mismatched_loop_start_parse() -> None:
    """Test the parser rejects mis-matched loop starts."""
    code = "++[["
    with pytest.raises(ParseError) as exc:
        parse_brainf(code)
    assert exc.value.msg == "Mis-matched '['!"


def test_mismatched_loop_end_parse() -> None:
    """Test the parser rejects mis-matched loop ends."""
    code = "++[]]]"
    with pytest.raises(ParseError) as exc:
        parse_brainf(code)
    assert exc.value.msg == "Mis-matched ']'!"


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
