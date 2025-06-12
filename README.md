# xdsl-bf

An optimising BrainF compiler in xDSL.

## The plan

- [ ] Write an mlir/xdsl dialect for bf using idrl
- [ ] Write something which parses source code into that dialect
- [ ] Write a lowering pass from our bf dialect to cf, arith, and builtin dialects
- [ ] Win (shared compiler infrastructure should take us the rest of the way with code gen and optimisations)

This is running concurrently with [my friend Aidan's effort in MLIR](https://gitlab.com/aidanhall/optimising-bf-compiler), so also have a look at that!
