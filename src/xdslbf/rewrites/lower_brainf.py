"""A pass which lowers the bf dialect to only use builtin dialects."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from xdsl.context import Context
from xdsl.dialects import arith, memref
from xdsl.dialects.builtin import ModuleOp, i32
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
class LshftOpLowering(RewritePattern):
    """A pattern to rewrite left shift operations."""

    const_1: arith.ConstantOp
    data_pointer: memref.AllocaOp

    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: bf.LshftOp, rewriter: PatternRewriter) -> None:
        """Rewrite left shift operations."""
        rewriter.replace_op(
            op,
            [
                load_op := memref.LoadOp.get(self.data_pointer, []),
                inc_op := arith.AddiOp(load_op, self.const_1),
                memref.StoreOp.get(inc_op, self.data_pointer, []),
            ],
        )


@dataclass
class IncOpLowering(RewritePattern):
    """A pattern to rewrite left shift operations."""

    const_1: arith.ConstantOp
    data_pointer: memref.AllocaOp
    memory: memref.AllocOp

    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: bf.IncOp, rewriter: PatternRewriter) -> None:
        """Rewrite increment operations."""
        rewriter.replace_op(
            op,
            [
                load_pointer_op := memref.LoadOp.get(self.data_pointer, []),
                load_data_op := memref.LoadOp.get(self.memory, [load_pointer_op]),
                inc_op := arith.AddiOp(load_data_op, self.const_1),
                memref.StoreOp.get(inc_op, self.memory, [load_pointer_op]),
            ],
        )


class LowerBfToBuiltinPass(ModulePass):
    """A pass for lowering operations in the bf dialect to only use builtin dialects."""

    name = "bf-to-builtin"

    def build_brainf_environment(
        self, _ctx: Context, op: ModuleOp, memory_size: int = 30_000
    ) -> tuple[arith.ConstantOp, memref.AllocaOp, memref.AllocOp]:
        """Build the brainf environment.

        This includes allocating the data pointer and the memory region.
        """
        runtime: list[Operation] = [
            const_0 := arith.ConstantOp.from_int_and_width(0, i32),
            const_1 := arith.ConstantOp.from_int_and_width(1, i32),
            data_pointer_alloca_op := memref.AllocaOp.get(i32, 32),
            memref.StoreOp.get(const_0, data_pointer_alloca_op, []),
            memory_alloc_op := memref.AllocOp.get(i32, 32, [memory_size]),
        ]

        first_block = op.regions[0].first_block
        assert first_block is not None
        first_op = first_block.first_op
        assert first_op is not None
        for new_op in runtime:
            first_block.insert_op_before(new_op, first_op)

        return (const_1, data_pointer_alloca_op, memory_alloc_op)

    def apply(self, ctx: Context, op: ModuleOp) -> None:
        """Apply the lowering pass."""
        const_1, data_pointer, memory = self.build_brainf_environment(ctx, op)

        PatternRewriteWalker(
            GreedyRewritePatternApplier(
                [
                    LshftOpLowering(const_1, data_pointer),
                    IncOpLowering(const_1, data_pointer, memory),
                ]
            )
        ).rewrite_module(op)
