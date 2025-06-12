# xdsl-bf

An optimising BrainF compiler in xDSL.

## The plan

- [x] Write a xDSL (IRDL) dialect for BrainF
- [x] Write a lexer and parser from program source code into this dialect
- [ ] Write a lowering pass from our BrainF dialect to MLIR's `cf`, `arith`, and `builtin` dialects
- [ ] Write an emulator for the BrainF dialect
- [ ] Write rewriting optimisations for the BrainF dialect

This is running concurrently with [my friend Aidan's effort in MLIR](https://gitlab.com/aidanhall/optimising-bf-compiler), so also have a look at that!
