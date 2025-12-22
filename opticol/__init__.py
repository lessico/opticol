__all__ = ["factories", "projector", "mapping", "mut_mapping", "mut_seq", "mut_set", "seq", "set"]

from opticol.projector import DefaultProjector

_default = DefaultProjector()

mapping = _default.mapping
mut_mapping = _default.mut_mapping
mut_seq = _default.mut_seq
mut_set = _default.mut_set
seq = _default.seq
set = _default.set

del DefaultProjector
