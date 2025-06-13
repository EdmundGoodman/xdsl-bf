"""A pass which lowers the bf dialect to only use builtin dialects."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from xdsl.context import Context
from xdsl.dialects import arith, memref, scf
from xdsl.dialects.builtin import ModuleOp, i32
from xdsl.ir import Block
from xdsl.passes import ModulePass
from xdsl.pattern_rewriter import (
    GreedyRewritePatternApplier,
    PatternRewriter,
    PatternRewriteWalker,
    RewritePattern,
    op_type_rewrite_pattern,
)

from xdslbf.dialects import bf

if TYPE_CHECKING:
    from xdsl.ir import Operation


@dataclass
class ShiftOpLowering(RewritePattern):
    """A pattern to rewrite left and right shift operations."""

    const_1: arith.ConstantOp
    data_pointer: memref.AllocaOp

    @op_type_rewrite_pattern
    def match_and_rewrite(
        self, op: bf.LshftOp | bf.RshftOp, rewriter: PatternRewriter
    ) -> None:
        """Rewrite left and right shift operations."""
        arith_op = arith.AddiOp if isinstance(op, bf.RshftOp) else arith.SubiOp
        rewriter.replace_op(
            op,
            [
                load_op := memref.LoadOp.get(self.data_pointer, []),
                inc_op := arith_op(load_op, self.const_1),
                memref.StoreOp.get(inc_op, self.data_pointer, []),
            ],
        )


@dataclass
class IncOpLowering(RewritePattern):
    """A pattern to rewrite increment and decrement operations."""

    const_1: arith.ConstantOp
    data_pointer: memref.AllocaOp
    memory: memref.AllocOp

    @op_type_rewrite_pattern
    def match_and_rewrite(
        self, op: bf.IncOp | bf.DecOp, rewriter: PatternRewriter
    ) -> None:
        """Rewrite increment and decrement operations."""
        arith_op = arith.AddiOp if isinstance(op, bf.IncOp) else arith.SubiOp
        rewriter.replace_op(
            op,
            [
                load_pointer_op := memref.LoadOp.get(self.data_pointer, []),
                load_data_op := memref.LoadOp.get(self.memory, [load_pointer_op]),
                inc_op := arith_op(load_data_op, self.const_1),
                memref.StoreOp.get(inc_op, self.memory, [load_pointer_op]),
            ],
        )


@dataclass
class LoopOpLowering(RewritePattern):
    """A pattern to rewrite loop operations."""

    const_0: arith.ConstantOp
    const_1: arith.ConstantOp
    data_pointer: memref.AllocaOp
    memory: memref.AllocOp

    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: bf.LoopOp, rewriter: PatternRewriter) -> None:
        """Rewrite loop operations."""
        # Extract and detach the body of the `bf.loop` operation
        op.detach_region(loop_body := op.regions[0])

        # Construct a while loop with the `bf.loop`'s body
        while_loop = scf.WhileOp(
            arguments=[],
            result_types=[],
            before_region=[
                Block(
                    [
                        load_pointer_op := memref.LoadOp.get(self.data_pointer, []),
                        load_data_op := memref.LoadOp.get(
                            self.memory, [load_pointer_op]
                        ),
                        cmp_op := arith.CmpiOp(load_data_op, self.const_0, "ne"),
                        scf.ConditionOp(cmp_op),
                    ]
                )
            ],
            after_region=loop_body,
        )

        # Replace the matched operation with the newly constructed while loop
        rewriter.replace_matched_op(while_loop)


@dataclass
class RetOpLowering(RewritePattern):
    """A pattern to rewrite return operations."""

    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: bf.RetOp, rewriter: PatternRewriter) -> None:
        """Rewrite ret operations."""
        rewriter.erase_op(op)


class LowerBfToBuiltinPass(ModulePass):
    """A pass for lowering operations in the bf dialect to only use builtin dialects."""

    name = "bf-to-builtin"

    def build_brainf_environment(
        self, _ctx: Context, op: ModuleOp, memory_size: int = 30_000
    ) -> tuple[arith.ConstantOp, arith.ConstantOp, memref.AllocaOp, memref.AllocOp]:
        """Build the brainf environment.

        This includes allocating the data pointer and the memory region.
        """
        # Instantiation the operations creating the runtime
        runtime: list[Operation] = [
            const_0 := arith.ConstantOp.from_int_and_width(0, i32),
            const_1 := arith.ConstantOp.from_int_and_width(1, i32),
            data_pointer_alloca_op := memref.AllocaOp.get(i32, 32),
            memref.StoreOp.get(const_0, data_pointer_alloca_op, []),
            memory_alloc_op := memref.AllocOp.get(i32, 32, [memory_size]),
        ]

        # Add the operations to the start of the module
        first_block = op.regions[0].first_block
        assert first_block is not None
        first_op = first_block.first_op
        assert first_op is not None
        for new_op in runtime:
            first_block.insert_op_before(new_op, first_op)

        # Return SSA references to operations used by the lowering passes
        return (const_0, const_1, data_pointer_alloca_op, memory_alloc_op)

    def apply(self, ctx: Context, op: ModuleOp) -> None:
        """Apply the lowering pass."""
        const_0, const_1, data_pointer, memory = self.build_brainf_environment(ctx, op)
        PatternRewriteWalker(
            GreedyRewritePatternApplier(
                [
                    ShiftOpLowering(const_1, data_pointer),
                    IncOpLowering(const_1, data_pointer, memory),
                    LoopOpLowering(const_0, const_1, data_pointer, memory),
                    RetOpLowering(),
                ]
            )
        ).rewrite_module(op)
