#!/usr/bin/env python3
"""Unit tests for the parser."""

import pytest
from xdsl.utils.exceptions import ParseError

from xdslbf.compiler import parse_brainf


def test_valid_parse() -> None:
    """Test the parser with example code exercising all instructions."""
    code = ",[>++<-]."
    parsed = parse_brainf(code)
    expected = """\
builtin.module {
  "in"() : () -> ()
  "loop"() : () -> ()
  "rshft"() : () -> ()
  "inc"() : () -> ()
  "inc"() : () -> ()
  "lshft"() : () -> ()
  "dec"() : () -> ()
  "ret"() : () -> ()
  "out"() : () -> ()
}"""
    assert str(parsed) == expected


def test_undefined_instructions_parse() -> None:
    """Test the parser rejects invalid characters."""
    code = "abc"
    with pytest.raises(ParseError) as exc:
        parse_brainf(code)
    assert exc.value.msg == "Unexpected character: a"
