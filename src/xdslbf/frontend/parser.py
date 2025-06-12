"""Parser for the BrainF language."""

from pathlib import Path

from xdsl.dialects.builtin import ModuleOp
from xdsl.parser import GenericParser, ParserState
from xdsl.utils.exceptions import ParseError
from xdsl.utils.lexer import Input

from xdslbf.dialects.bf import (
    BrainFOperation,
    DecOp,
    IncOp,
    InOp,
    LoopOp,
    LshftOp,
    OutOp,
    RetOp,
    RshftOp,
)
from xdslbf.frontend.lexer import BrainFLexer, BrainFTokenKind

OPERATION_LOOKUP: dict[BrainFTokenKind, type[BrainFOperation]] = {
    BrainFTokenKind.PLUS: IncOp,
    BrainFTokenKind.MINUS: DecOp,
    BrainFTokenKind.LT: LshftOp,
    BrainFTokenKind.GT: RshftOp,
    BrainFTokenKind.SBRACKET_OPEN: LoopOp,
    BrainFTokenKind.SBRACKET_CLOSE: RetOp,
    BrainFTokenKind.DOT: OutOp,
    BrainFTokenKind.COMMA: InOp,
}


class BrainFParser(GenericParser[BrainFTokenKind]):
    """Parser for the BrainF language."""

    def __init__(self, file: Path, program: str):
        """Instantiate the parser with the lexer."""
        super().__init__(ParserState(BrainFLexer(Input(program, str(file)))))

    def parse(self) -> ModuleOp:
        """Parser a BrainF program."""
        ops: list[BrainFOperation] = []

        while True:
            token = self._consume_token()
            if token.kind == BrainFTokenKind.EOF:
                break
            if token.kind in OPERATION_LOOKUP:
                ops.append(OPERATION_LOOKUP[token.kind]())
            else:
                raise ParseError(token.span, "Unsupported token!")

        return ModuleOp(ops)  # pyright: ignore[reportArgumentType]
