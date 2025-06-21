"""A pass which lowers the bf dialect to use only builtin mlir dialects."""

from dataclasses import dataclass

from xdsl.context import Context
from xdsl.dialects import arith
from xdsl.dialects.builtin import IndexType, ModuleOp, i32
from xdsl.ir import Operation, SSAValue
from xdsl.passes import ModulePass
from xdsl.pattern_rewriter import (
    PatternRewriter,
    PatternRewriteWalker,
    RewritePattern,
    op_type_rewrite_pattern,
)

from xdslbf.dialects import bf, bfe


@dataclass
class BfOpLowering(RewritePattern):
    """A pattern to rewrite bf as bfe operations."""

    data_pointer_stack: list[Operation | SSAValue]

    def _rewrite_into_mem_op(
        self, rewriter: PatternRewriter, body: list[Operation]
    ) -> None:
        """Rewrite a matched operation into the body of a memory operation."""
        mem_op = bfe.MemoryOp(pointer=self.data_pointer_stack[-1])
        assert mem_op.body.first_block is not None
        mem_op.body.first_block.add_ops(body)
        rewriter.insert_op_before_matched_op(mem_op)
        rewriter.erase_matched_op()
        self.data_pointer_stack[-1] = mem_op

    def rewrite_inc_op(self, op: bf.BrainFOperation, rewriter: PatternRewriter) -> None:
        """Rewrite an increment operation."""
        assert isinstance(op, bf.IncOp | bf.DecOp)
        arith_op = arith.AddiOp if isinstance(op, bf.IncOp) else arith.SubiOp
        self._rewrite_into_mem_op(
            rewriter,
            [
                data := bfe.LoadOp(0),
                const_1 := arith.ConstantOp.from_int_and_width(1, i32),
                incremented := arith_op(data, const_1),
                bfe.StoreOp(incremented, 0),
            ],
        )

    def rewrite_in_op(self, op: bf.BrainFOperation, rewriter: PatternRewriter) -> None:
        """Rewrite a input operation."""
        assert isinstance(op, bf.InOp)
        self._rewrite_into_mem_op(
            rewriter,
            [
                data := bfe.InOp(),
                bfe.StoreOp(data, 0),
            ],
        )

    def rewrite_out_op(self, op: bf.BrainFOperation, rewriter: PatternRewriter) -> None:
        """Rewrite a input operation."""
        assert isinstance(op, bf.OutOp)
        self._rewrite_into_mem_op(
            rewriter,
            [
                data := bfe.LoadOp(0),
                bfe.OutOp(data),
            ],
        )

    def rewrite_shift_op(
        self, op: bf.BrainFOperation, rewriter: PatternRewriter
    ) -> None:
        """Rewrite a shift operation."""
        assert isinstance(op, bf.LshftOp | bf.RshftOp)
        mem_op = bfe.MemoryOp(
            pointer=self.data_pointer_stack[-1],
            move=1 if isinstance(op, bf.RshftOp) else -1,
        )
        rewriter.insert_op_before_matched_op(mem_op)
        rewriter.erase_matched_op()
        self.data_pointer_stack[-1] = mem_op

    def rewrite_loop_op(
        self, op: bf.BrainFOperation, rewriter: PatternRewriter
    ) -> None:
        """Rewrite a loop operation."""
        assert isinstance(op, bf.LoopOp)
        # Extract and detach the body of the `bf.loop` operation
        loop_body = op.regions
        for region in loop_body:
            op.detach_region(region)
        # Construct a while loop with the `bf.loop`'s body
        while_op = bfe.WhileOp(
            pointer=self.data_pointer_stack[-1],
            regions=loop_body,
        )
        assert while_op.body.first_block is not None
        # Add the new op after the matched one so its body also gets lowered
        rewriter.insert_op_after_matched_op(while_op)
        # Erase the matched op
        rewriter.erase_matched_op()
        self.data_pointer_stack[-1] = while_op
        self.data_pointer_stack.append(while_op.operands[0])

    def rewrite_ret_op(self, op: bf.BrainFOperation, rewriter: PatternRewriter) -> None:
        """Rewrite a return operation."""
        assert isinstance(op, bf.RetOp)
        rewriter.replace_matched_op(bfe.ContinueOp(self.data_pointer_stack[-1]))
        self.data_pointer_stack.pop()

    @op_type_rewrite_pattern
    def match_and_rewrite(
        self, op: bf.BrainFOperation, rewriter: PatternRewriter
    ) -> None:
        """Rewrite bf as bfe operations."""
        match type(op):
            case bf.IncOp | bf.DecOp:
                self.rewrite_inc_op(op, rewriter)
            case bf.InOp:
                self.rewrite_in_op(op, rewriter)
            case bf.OutOp:
                self.rewrite_out_op(op, rewriter)
            case bf.LshftOp | bf.RshftOp:
                self.rewrite_shift_op(op, rewriter)
            case bf.LoopOp:
                self.rewrite_loop_op(op, rewriter)
            case bf.RetOp:
                self.rewrite_ret_op(op, rewriter)
            case _:
                pass


class LowerBfToBfePass(ModulePass):
    """A pass for lowering operations in the bf dialect to only use builtin dialects."""

    name = "bf-to-bfe"

    def apply(self, ctx: Context, op: ModuleOp) -> None:  # noqa: ARG002
        """Apply the lowering pass."""
        pointer_start = arith.ConstantOp.from_int_and_width(0, IndexType())
        block = op.body.first_block
        assert block
        if block.first_op is not None:
            block.insert_op_before(pointer_start, block.first_op)
        else:
            block.add_op(pointer_start)

        PatternRewriteWalker(BfOpLowering([pointer_start])).rewrite_module(op)
