# xdsl-bf

An optimising BrainF compiler in xDSL.

## The plan

- [x] Design a dialect for BrainF
- [x] Implement a lexer and parser from program source code into this dialect
- [x] Implement an interpreter for the BrainF dialect
- [x] Implement a lowering pass from our BrainF dialect to MLIR's `cf`, `arith`,  `builtin`, `memref`, and `llvm` dialects
- [ ] Implement rewriting optimisations for the BrainF dialect
  - [ ] Design an extended dialect for optimising BrainF
  - [ ] Implement lowering passes to and from the extended dialect
  - [ ] Implement optimisation passes on the extended dialect

This is running concurrently with [my friend Aidan's effort in MLIR](https://gitlab.com/aidanhall/optimising-bf-compiler), so also have a look at that!

## Resources and prior art

- <https://en.wikipedia.org/wiki/Brainfuck#Language_design>
- <https://github.com/ibara/bf.ssa?tab=readme-ov-file>
- <https://github.com/pretzelhammer/rust-blog/blob/master/posts/too-many-brainfuck-compilers.md>
- <https://rodrigodd.github.io/2022/11/26/bf_compiler-part3.html>
- <https://eli.thegreenplace.net/2017/adventures-in-jit-compilation-part-3-llvm/>
- <https://blog.dubbelboer.com/2012/11/18/brainfuck-jit.html>
