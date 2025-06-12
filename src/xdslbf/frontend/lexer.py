"""Lexer for the BrainF language."""

from enum import Enum, auto
from typing import TypeAlias

from xdsl.utils.exceptions import ParseError
from xdsl.utils.lexer import Lexer, Span, Token


class BrainFTokenKind(Enum):
    """Tokens for the BrainF language."""

    PLUS = auto()
    MINUS = auto()
    LT = auto()
    GT = auto()
    SBRACKET_OPEN = auto()
    SBRACKET_CLOSE = auto()
    DOT = auto()
    COMMA = auto()
    EOF = auto()


TOKEN_LOOKUP: dict[str | None, BrainFTokenKind] = {
    "+": BrainFTokenKind.PLUS,
    "-": BrainFTokenKind.MINUS,
    "<": BrainFTokenKind.LT,
    ">": BrainFTokenKind.GT,
    "[": BrainFTokenKind.SBRACKET_OPEN,
    "]": BrainFTokenKind.SBRACKET_CLOSE,
    ".": BrainFTokenKind.DOT,
    ",": BrainFTokenKind.COMMA,
    None: BrainFTokenKind.EOF,
}

BrainFToken: TypeAlias = Token[BrainFTokenKind]


class BrainFLexer(Lexer[BrainFTokenKind]):
    """Lexer for the BrainF language."""

    def _get_char(self) -> str | None:
        """Get the character at the current location, or None if out of bounds."""
        res = self.input.slice(self.pos, self.pos + 1)
        self.pos += 1
        return res

    def lex(self) -> BrainFToken:
        """Lex the program."""
        if (current_char := self._get_char()) in TOKEN_LOOKUP:
            return self._form_token(TOKEN_LOOKUP[current_char], self.pos)

        raise ParseError(
            Span(self.pos, self.pos + 1, self.input),
            f"Unexpected character: {current_char}",
        )
