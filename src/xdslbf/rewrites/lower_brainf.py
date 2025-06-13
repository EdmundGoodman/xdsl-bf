"""A pass which lowers the bf dialect to only use builtin dialects."""

from xdsl.context import Context
from xdsl.dialects.builtin import ModuleOp
from xdsl.passes import ModulePass
from xdsl.pattern_rewriter import (
    GreedyRewritePatternApplier,
    PatternRewriter,
    PatternRewriteWalker,
    RewritePattern,
    op_type_rewrite_pattern,
)

from xdslbf.dialects import bf


class LshftOpLowering(RewritePattern):
    """A pattern to rewrite left shift operations."""

    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: bf.LshftOp, rewriter: PatternRewriter) -> None:
        """Rewrite left shift operations."""
        raise NotImplementedError("Left shift lowering not implemented!")


class LowerBfToBuiltinPass(ModulePass):
    """A pass for lowering operations in the bf dialect to only use builtin dialects."""

    name = "bf-to-builtin"

    def apply(self, ctx: Context, op: ModuleOp) -> None:  # noqa: ARG002
        """Apply the lowering pass."""
        PatternRewriteWalker(
            GreedyRewritePatternApplier(
                [
                    LshftOpLowering(),
                ]
            )
        ).rewrite_module(op)
