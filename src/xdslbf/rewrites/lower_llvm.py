"""A pass which lowers builtin lowering of bf to a llvm-backed executable."""

from xdsl.context import Context
from xdsl.dialects import arith, func, llvm
from xdsl.dialects.builtin import ModuleOp, i32
from xdsl.ir import Block, Region
from xdsl.passes import ModulePass
from xdsl.pattern_rewriter import (
    GreedyRewritePatternApplier,
    PatternRewriteWalker,
)
from xdsl.transforms.printf_to_llvm import PrintlnOpToPrintfCall


class LowerBfBuiltinToLlvmExecutablePass(ModulePass):
    """A pass for lowering from the builtin lowering of bf to an LLVM executable."""

    name = "bf-builtin-to-llvm-exectuable"

    def build_executable(self, _ctx: Context, op: ModuleOp) -> None:
        """Build the brainf environment.

        This includes wrapping the module with a main function and printf bindings.
        """
        op.detach_region(region := op.body)
        op.add_region(
            Region(
                block := Block(
                    [main_func := func.FuncOp("main", ((), (i32,)), region=region)]
                )
            )
        )
        region.block.add_ops(
            [
                const_0 := arith.ConstantOp.from_int_and_width(0, i32),
                func.ReturnOp(const_0),
            ]
        )
        block.insert_op_before(
            llvm.FuncOp(
                "printf",
                llvm.LLVMFunctionType(
                    [llvm.LLVMPointerType.opaque()], is_variadic=True
                ),
                linkage=llvm.LinkageAttr("external"),
            ),
            main_func,
        )

    def apply(self, ctx: Context, op: ModuleOp) -> None:
        """Apply the lowering pass."""
        self.build_executable(ctx, op)

        add_printf_call = PrintlnOpToPrintfCall()
        PatternRewriteWalker(
            GreedyRewritePatternApplier(
                [
                    add_printf_call,
                ]
            )
        ).rewrite_module(op)

        if add_printf_call.collected_global_symbs:
            op.body.block.add_ops(add_printf_call.collected_global_symbs.values())
