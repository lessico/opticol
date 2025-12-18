from abc import ABC, abstractmethod
from collections.abc import Mapping, MutableMapping, MutableSequence, MutableSet, Sequence, Set

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

    @abstractmethod
    def mapping[K, V](self, mapping: Mapping[K, V]) -> Mapping[K, V]: ...

    @abstractmethod
    def mut_mapping[K, V](self, mut_mapping: MutableMapping[K, V]) -> MutableMapping[K, V]: ...


class PassThroughProjector(ABC):
    def seq[T](self, seq: Sequence[T]) -> Sequence[T]:
        return seq

    def mut_seq[T](self, mut_seq: MutableSequence[T]) -> MutableSequence[T]:
        return mut_seq

    def set[T](self, s: Set[T]) -> Set[T]:
        return s

    def mut_set[T](self, mut_set: MutableSet[T]) -> MutableSet[T]:
        return mut_set

    def mapping[K, V](self, mapping: Mapping[K, V]) -> Mapping[K, V]:
        return mapping

    def mut_mapping[K, V](self, mut_mapping: MutableMapping[K, V]) -> MutableMapping[K, V]:
        return mut_mapping


class DefaultOptimizingProjector(Projector):
    def seq[T](self, seq: Sequence[T]) -> Sequence[T]:
        return opticol.seq(seq)

    def mut_seq[T](self, mut_seq: MutableSequence[T]) -> MutableSequence[T]:
        return opticol.mut_seq(mut_seq)

    def set[T](self, s: Set[T]) -> Set[T]:
        return opticol.set(s)

    def mut_set[T](self, mut_set: MutableSet[T]) -> MutableSet[T]:
        return opticol.mut_set(mut_set)

    def mapping[K, V](self, mapping: Mapping[K, V]) -> Mapping[K, V]:
        return opticol.mapping(mapping)

    def mut_mapping[K, V](self, mut_mapping: MutableMapping[K, V]) -> MutableMapping[K, V]:
        return opticol.mut_mapping(mut_mapping)
