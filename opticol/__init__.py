"""Convenient access to a default collection projection policy.

This module provides quick-access functions for creating optimized collections using a sensible
default projector configuration. These functions (seq, mut_seq, set, mut_set, mapping, mut_mapping)
are backed by a default OptimizedCollectionProjector instance configured for collections of size
0-3. This projector instance can be accessed by the `default` member as well.

For more control over optimization strategy, consumers should use the Projector API directly (see
opticol.projector). Projectors provide a pluggable policy layer that allows different optimization
approaches to be swapped based on use case. The factory module (factory.py) contains the underlying
implementation that generates optimized collection classes of arbitrary sizes.

Example:
    >>> import opticol
    >>> s = opticol.seq([1, 2, 3])  # Creates optimized sequence
    >>> m = opticol.mapping({'a': 1, 'b': 2})  # Creates optimized mapping
"""

__all__ = ["factory", "projector", "mapping", "mut_mapping", "mut_seq", "mut_set", "seq", "set"]

from opticol.projector import OptimizedCollectionProjector

default = OptimizedCollectionProjector(0, 3, True)
"""
The projector instance that implements the logic of the module level convenience functions.
"""

mapping = default.mapping
mut_mapping = default.mut_mapping
mut_seq = default.mut_seq
mut_set = default.mut_set
seq = default.seq
set = default.set

del OptimizedCollectionProjector
