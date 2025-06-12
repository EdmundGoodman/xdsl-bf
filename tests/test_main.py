#!/usr/bin/env python3
"""Unit tests for the main methods."""

from xdslbf.main import get_greeting


def test_get_greeting() -> None:
    """Test getting the greeting string."""
    assert get_greeting().startswith("Hello")
