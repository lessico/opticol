__all__ = [
    "mapping",
    "mutable_mapping",
    "mutable_sequence",
    "mutable_set",
    "projector",
    "sequence",
    "set",
]

from opticol import mutable_mapping, mutable_sequence, mutable_set, sequence
from opticol import mapping as _mapping_module
from opticol import set as _set_module

mapping = _mapping_module.project
mut_mapping = mutable_mapping.project
mut_seq = mutable_sequence.project
mut_set = mutable_set.project
seq = sequence.project
set = _set_module.project

del _mapping_module
del mutable_mapping
del mutable_sequence
del mutable_set
del sequence
del _set_module
