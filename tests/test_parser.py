#!/usr/bin/env python3
"""Unit tests for the parser."""

from xdslbf.compiler import parse_brainf


def test_parser() -> None:
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
