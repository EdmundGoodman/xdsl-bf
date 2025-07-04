"""A pass which lowers the bf dialect to use only builtin mlir dialects."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from xdsl.context import Context
from xdsl.dialects import arith, func, memref, scf
from xdsl.dialects.builtin import IndexType, ModuleOp, i32
from xdsl.ir import Block, Region
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
                const_1 := arith.ConstantOp.from_int_and_width(1, i32),
                inc_op := arith_op(load_op, const_1),
                memref.StoreOp.get(inc_op, self.data_pointer, []),
            ],
        )


@dataclass
class IncOpLowering(RewritePattern):
    """A pattern to rewrite increment and decrement operations."""

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
                pointer_index := arith.IndexCastOp(load_pointer_op, IndexType()),
                load_data_op := memref.LoadOp.get(self.memory, [pointer_index]),
                const_1 := arith.ConstantOp.from_int_and_width(1, i32),
                inc_op := arith_op(load_data_op, const_1),
                memref.StoreOp.get(inc_op, self.memory, [pointer_index]),
            ],
        )


@dataclass
class LoopOpLowering(RewritePattern):
    """A pattern to rewrite loop operations."""

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
                        pointer_index := arith.IndexCastOp(
                            load_pointer_op, IndexType()
                        ),
                        load_data_op := memref.LoadOp.get(self.memory, [pointer_index]),
                        const_0 := arith.ConstantOp.from_int_and_width(0, i32),
                        cmp_op := arith.CmpiOp(load_data_op, const_0, "ne"),
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
        rewriter.replace_op(op, scf.YieldOp())


@dataclass
class OutOpLowering(RewritePattern):
    """A pattern to rewrite output operations."""

    data_pointer: memref.AllocaOp
    memory: memref.AllocOp

    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: bf.OutOp, rewriter: PatternRewriter) -> None:
        """Rewrite output operations."""
        rewriter.insert_op_before_matched_op(
            [
                load_pointer_op := memref.LoadOp.get(self.data_pointer, []),
                pointer_index := arith.IndexCastOp(load_pointer_op, IndexType()),
                load_data_op := memref.LoadOp.get(self.memory, [pointer_index]),
                func.CallOp("putchar", [load_data_op], [i32]),
            ]
        )
        rewriter.erase_op(op)


@dataclass
class InOpLowering(RewritePattern):
    """A pattern to rewrite input operations."""

    data_pointer: memref.AllocaOp
    memory: memref.AllocOp

    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: bf.InOp, rewriter: PatternRewriter) -> None:
        """Rewrite input operations."""
        rewriter.insert_op_before_matched_op(
            [
                data := func.CallOp("getchar", [], [i32]),
                load_pointer_op := memref.LoadOp.get(self.data_pointer, []),
                pointer_index := arith.IndexCastOp(load_pointer_op, IndexType()),
                memref.StoreOp.get(data, self.memory, [pointer_index]),
            ]
        )
        rewriter.erase_op(op)


class LowerBfToBuiltinPass(ModulePass):
    """A pass for lowering operations in the bf dialect to only use builtin dialects."""

    name = "bf-to-builtin"

    def build_brainf_environment(
        self, _ctx: Context, op: ModuleOp, memory_size: int = 30_000
    ) -> tuple[memref.AllocaOp, memref.AllocOp]:
        """Build the brainf environment.

        This includes allocating the data pointer and the memory region.
        """
        # Lift the ir into a main function
        op.detach_region(region := op.body)
        block = region.block
        op.add_region(
            Region(
                outer_block := Block([func.FuncOp("main", ((), (i32,)), region=region)])
            )
        )

        # Instantiate the operations to register IO functions
        setup: list[Operation] = [
            func.FuncOp.external("putchar", (i32,), (i32,)),
            func.FuncOp.external("getchar", (), (i32,)),
        ]
        assert outer_block.first_op is not None
        for new_op in setup:
            outer_block.insert_op_before(new_op, outer_block.first_op)

        # Instantiate the operations setting up the runtime
        setup: list[Operation] = [
            const_0 := arith.ConstantOp.from_int_and_width(0, i32),
            data_pointer_alloca_op := memref.AllocaOp.get(i32, 64, []),
            memref.StoreOp.get(const_0, data_pointer_alloca_op, []),
            memory_alloc_op := memref.AllocOp.get(i32, 64, [memory_size]),
        ]
        first_op = block.first_op
        if first_op is not None:
            block.insert_ops_before(setup, first_op)
        else:
            block.add_ops(setup)

        # Instantiate the operations tearing down up the runtime
        block.add_ops(
            [
                memref.DeallocOp.get(memory_alloc_op),
                const_0 := arith.ConstantOp.from_int_and_width(0, i32),
                func.ReturnOp(const_0),
            ]
        )

        # Return SSA references to operations used by the lowering passes
        return (data_pointer_alloca_op, memory_alloc_op)

    def apply(self, ctx: Context, op: ModuleOp) -> None:
        """Apply the lowering pass."""
        data_pointer, memory = self.build_brainf_environment(ctx, op)
        PatternRewriteWalker(
            GreedyRewritePatternApplier(
                [
                    ShiftOpLowering(data_pointer),
                    IncOpLowering(data_pointer, memory),
                    LoopOpLowering(data_pointer, memory),
                    RetOpLowering(),
                    InOpLowering(data_pointer, memory),
                    OutOpLowering(data_pointer, memory),
                ]
            )
        ).rewrite_module(op)
