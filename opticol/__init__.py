__all__ = ["mutable_sequence", "projector", "sequence"]

from opticol import mutable_sequence, sequence

mut_seq = mutable_sequence.project
seq = sequence.project

del mutable_sequence
del sequence
