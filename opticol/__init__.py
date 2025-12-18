__all__ = ["mutable_sequence", "mutable_set", "projector", "sequence", "set"]

from opticol import mutable_sequence, mutable_set, sequence
from opticol import set as _set_module

mut_seq = mutable_sequence.project
mut_set = mutable_set.project
seq = sequence.project
set = _set_module.project

del mutable_sequence
del mutable_set
del sequence
del _set_module
