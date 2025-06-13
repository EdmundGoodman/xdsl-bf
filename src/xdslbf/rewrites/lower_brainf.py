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
        raise NotImplementedError
        # i32_type = builtin.i32
        # index_type = builtin.IndexType()
        # memref_type = memref. MemRefType([1], i32_type)
        # c0 = arith.Constant.from_int_and_width(0, index_type)
        # c1 = arith.Constant.from_int_and_width(1, i32_type)
        # load_op = memref.LoadOp()
        # add_op = arith.AddiOp(load_op.result, )
        # store_op = memref.Store.get(add_op.result, memref_arg, [c0.result])
        # const_1 = arith.ConstantOp(builtin.IntegerAttr(1, i32))
        # rewriter.insert_op_after_matched_op([const_1])
        # rewriter.erase_matched_op()


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
