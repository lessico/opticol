from abc import ABC, abstractmethod
from collections.abc import MutableSequence, MutableSet, Sequence, Set

import opticol


class Projector(ABC):
    @abstractmethod
    def seq[T](self, seq: Sequence[T]) -> Sequence[T]: ...

    @abstractmethod
    def mut_seq[T](self, mut_seq: MutableSequence[T]) -> MutableSequence[T]: ...

    @abstractmethod
    def set[T](self, s: Set[T]) -> Set[T]: ...

    @abstractmethod
    def mut_set[T](self, mut_set: MutableSet[T]) -> MutableSet[T]: ...


class PassThroughProjector(ABC):
    def seq[T](self, seq: Sequence[T]) -> Sequence[T]:
        return seq

    def mut_seq[T](self, mut_seq: MutableSequence[T]) -> MutableSequence[T]:
        return mut_seq

    def set[T](self, s: Set[T]) -> Set[T]:
        return s

    def mut_set[T](self, mut_set: MutableSet[T]) -> MutableSet[T]:
        return mut_set


class DefaultOptimizingProjector(Projector):
    def seq[T](self, seq: Sequence[T]) -> Sequence[T]:
        return opticol.seq(seq)

    def mut_seq[T](self, mut_seq: MutableSequence[T]) -> MutableSequence[T]:
        return opticol.mut_seq(mut_seq)

    def set[T](self, s: Set[T]) -> Set[T]:
        return opticol.set(s)

    def mut_set[T](self, mut_set: MutableSet[T]) -> MutableSet[T]:
        return opticol.mut_set(mut_set)
