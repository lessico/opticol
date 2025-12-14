from abc import ABC, abstractmethod
from collections.abc import Sequence, MutableSequence

from opticol import mutable_sequence, sequence


class Projector(ABC):
    @abstractmethod
    def seq[T](self, seq: Sequence[T]) -> Sequence[T]: ...

    @abstractmethod
    def mut_seq[T](self, mut_seq: MutableSequence[T]) -> MutableSequence[T]: ...


class PassThroughProjector(ABC):
    def seq[T](self, seq: Sequence[T]) -> Sequence[T]:
        return seq

    def mut_seq[T](self, mut_seq: MutableSequence[T]) -> MutableSequence[T]:
        return mut_seq


class DefaultOptimizingProjector(Projector):
    def seq[T](self, seq: Sequence[T]) -> Sequence[T]:
        return sequence.project(seq)

    def mut_seq[T](self, mut_seq: MutableSequence[T]) -> MutableSequence[T]:
        return mutable_sequence.project(mut_seq)
