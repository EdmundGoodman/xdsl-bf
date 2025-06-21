"""A pass which lowers the bfe dialect to use only builtin mlir dialects."""

from xdsl.context import Context
from xdsl.dialects import arith, cf, func, memref, scf
from xdsl.dialects.builtin import IndexType, ModuleOp, i32
from xdsl.ir import Block, Region
from xdsl.passes import ModulePass
from xdsl.printer import Printer
from xdsl.rewriter import BlockInsertPoint, Rewriter

from xdslbf.dialects import bfe

PRINTER = Printer()


class LowerBfeToBuiltinPass(ModulePass):
    """A pass for lowering operations in the bfe dialect to only use builtin dialects."""

    name = "bfe-to-builtin"

    def build_brainf_environment(
        self, _ctx: Context, op: ModuleOp, memory_size: int = 30_000
    ) -> tuple[func.FuncOp, memref.AllocOp]:
        """Build the brainf environment.

        This includes allocating the data pointer and the memory region.
        """
        # Lift the ir into a main function
        op.detach_region(region := op.body)
        # block = region.block
        op.add_region(
            Region(
                module_block := Block(
                    [main := func.FuncOp("main", ((), (i32,)), region=region)]
                )
            )
        )

        # Instantiate the operations to register IO functions
        assert module_block.first_op is not None
        module_block.insert_ops_before(
            [
                func.FuncOp.external("getchar", (), (i32,)),
                func.FuncOp.external("putchar", (i32,), (i32,)),
            ],
            module_block.first_op,
        )

        # Move the pointer initialisation into the runtime setup block
        assert main.body.first_block is not None
        assert main.body.first_block.first_op is not None
        (const_move := main.body.first_block.first_op).detach()
        # Instantiate the operations setting up the runtime
        setup = Block(
            [
                memory_alloc_op := memref.AllocOp.get(i32, 64, [memory_size]),
                const_move,
                cf.BranchOp(main.body.block, const_move),
            ]
        )
        main.body.insert_block_before(setup, main.body.first_block)

        # # Instantiate the operations tearing down up the runtime
        teardown = Block(
            [
                memref.DeallocOp.get(memory_alloc_op),
                const_0 := arith.ConstantOp.from_int_and_width(0, i32),
                func.ReturnOp(const_0),
            ],
            arg_types=[IndexType()],
        )
        assert main.body.last_block is not None
        main.body.last_block.add_op(cf.BranchOp(teardown, const_move))
        main.body.insert_block_after(teardown, main.body.last_block)

        return main, memory_alloc_op

    def lower_bfe_blocks(self, main: func.FuncOp, memory: memref.AllocOp) -> None:  # noqa: ARG002
        """Convert all bfe ops to llvm and scf equivalents."""
        main_impl_block = main.body.blocks[1]
        prev_block = main.body.last_block
        assert prev_block is not None
        # print(main)

        # Elide the temporary basic block routing during walk
        assert isinstance(main_impl_block.last_op, cf.BranchOp)
        main_impl_block.last_op.detach()

        # Walk the main implementation
        for op in main_impl_block.walk(reverse=True):
            # print(op.name)
            if isinstance(op, bfe.MemoryOp):
                mem_block = op.body.detach_block(0)
                mem_block.insert_arg(IndexType(), 0)
                if move_offset := op.get_move():
                    mem_block.add_ops(
                        [
                            const_move_offset := arith.ConstantOp.from_int_and_width(
                                move_offset, IndexType()
                            ),
                            move := arith.AddiOp(mem_block.args[0], const_move_offset),
                        ]
                    )
                else:
                    move = mem_block.args[0]
                mem_block.add_op(cf.BranchOp(prev_block, move))
                PRINTER.print(mem_block)
                Rewriter().insert_block(
                    mem_block,
                    BlockInsertPoint.after(main_impl_block),
                )
                prev_block = mem_block

            elif isinstance(op, bfe.WhileOp):
                op.detach_region(loop_region := op.regions[0])
                loop_block = Block(
                    [
                        scf.WhileOp(
                            arguments=[],
                            result_types=[],
                            before_region=[
                                Block(
                                    [
                                        # load_pointer_op := memref.LoadOp.get(self.data_pointer, []),
                                        # pointer_index := arith.IndexCastOp(
                                        #     load_pointer_op, IndexType()
                                        # ),
                                        # load_data_op := memref.LoadOp.get(self.memory, [pointer_index]),
                                        const_0 := arith.ConstantOp.from_int_and_width(
                                            0, i32
                                        ),
                                        # cmp_op := arith.CmpiOp(load_data_op, const_0, "ne"),
                                        scf.ConditionOp(const_0),
                                    ]
                                )
                            ],
                            after_region=loop_region,
                        )
                    ],
                    arg_types=(IndexType(),),
                )
                move = loop_block.args[0]
                loop_block.add_op(cf.BranchOp(prev_block, move))
                PRINTER.print(loop_block)
                Rewriter().insert_block(
                    loop_block,
                    BlockInsertPoint.after(main_impl_block),
                )
                prev_block = loop_block

            else:
                pass
                # raise PassFailedException(f"Unexpected operation '{op.name}'")

        # Discard the original main implementation
        main.body.detach_block(main_impl_block)

    def apply(self, ctx: Context, op: ModuleOp) -> None:
        """Apply the lowering pass."""
        main, memory = self.build_brainf_environment(ctx, op)
        self.lower_bfe_blocks(main, memory)
        print("\n\n")
        # PatternRewriteWalker(
        #     GreedyRewritePatternApplier(
        #         [
        #             MemoryOpLowering(memory),
        #         ]
        #     )
        # ).rewrite_module(op)
