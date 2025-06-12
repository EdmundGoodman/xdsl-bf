# xdsl-bf

An optimising BrainF compiler in xDSL.

## The plan

- [ ] Write an mlir/xdsl dialect for bf using idrl (only 6 ops so should be speedy)
- [ ] Write something which parses source code into that dialect
- [ ] Write a lowering pass from our bf dialect to cf, arith, and builtin dialects
- [ ] Win (shared compiler infrastructure should take us the rest of the way with code gen and optimisations)
