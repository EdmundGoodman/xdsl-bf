"""A pass which lowers the bf dialect to use only builtin mlir dialects."""

from xdsl.context import Context
from xdsl.dialects.builtin import ModuleOp
from xdsl.passes import ModulePass
from xdsl.pattern_rewriter import (
    PatternRewriter,
    PatternRewriteWalker,
    RewritePattern,
    op_type_rewrite_pattern,
)

from xdslbf.dialects import bfe


class MergeBfeMemoryOp(RewritePattern):
    """A pattern to merge adjacent bfe memory operations."""

    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: bfe.MemoryOp, rewriter: PatternRewriter) -> None:
        """Merge adjacent bfe memory operations."""
        # We want to merge adjacent paris of memory operations
        if not isinstance(next_op := op.next_op, bfe.MemoryOp):
            return

        # Make a new operation which takes the current pointer offset
        merged_op = bfe.MemoryOp(
            pointer=op.operands[0],
            move=(next_offset := op.move.value.data) + next_op.move.value.data,
        )

        # Plumb through SSA values of all first operation stores and second
        # operation loads, with the correctly updated offsets

        assert merged_op.body.first_block is not None
        stored_operation: dict[int, bfe.StoreOp] = {}
        for inner_op in op.body.ops:
            if isinstance(inner_op, bfe.StoreOp):
                # Track the offsets written to by the first operation
                stored_operation[inner_op.get_offset()] = inner_op
            # Copy all operations across to the merged operation
            inner_op.detach()
            merged_op.body.first_block.add_op(inner_op)

        for inner_op in next_op.body.ops:
            if isinstance(inner_op, bfe.StoreOp | bfe.LoadOp):
                # Update the offsets to reflect moves
                inner_op.set_offset(next_offset + inner_op.get_offset())
            if (
                isinstance(inner_op, bfe.LoadOp)
                and (offset := next_offset + inner_op.get_offset()) in stored_operation
            ):
                # If we are loading back something we just stored, replace all
                # the re-load uses with the original value stored, and discard
                # the extraneous store
                inner_op.results[0].replace_by(stored_operation[offset].data)
                rewriter.erase_op(stored_operation[offset])
                continue
            # Copy non-load other operations across to the merged operation
            inner_op.detach()
            merged_op.body.first_block.add_op(inner_op)

        rewriter.replace_op(next_op, merged_op)
        rewriter.erase_matched_op()


class OptimiseBfePass(ModulePass):
    """A pass for optimising the bfe dialect."""

    name = "optimise-bfe"

    def apply(self, ctx: Context, op: ModuleOp) -> None:  # noqa: ARG002
        """Apply the lowering pass."""
        PatternRewriteWalker(MergeBfeMemoryOp()).rewrite_module(op)
