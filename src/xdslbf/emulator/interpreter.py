"""Interpreter for the BrainF language.

Approach sketch:

```python
from typing import Any

from xdsl.interpreter import (
    Interpreter,
    InterpreterFunctions,
    impl_terminator,
    register_impls,
)

from xdslbf.dialects import bf


@register_impls
class BrainFFunctions(InterpreterFunctions):
    '''Implementations for the operations of the BrainF language.'''

    @impl_terminator(bf.IncOp)
    def run_inc(
        self, interpreter: Interpreter, op: bf.IncOp, args: tuple[Any, ...]
    ) -> tuple[Any, ...]:
        '''Implementation for the increment operation.'''
        raise NotImplementedError
```
"""
