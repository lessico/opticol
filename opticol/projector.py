from abc import ABC, abstractmethod
from collections.abc import (
    Callable,
    Iterable,
    Sized,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Set,
)
from typing import TypeVar

from opticol.factories import (
    create_mapping_class,
    create_mut_mapping_class,
    create_mut_seq_class,
    create_mut_set_class,
    create_seq_class,
    create_set_class,
)


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



class DefaultProjector(Projector):
    @staticmethod
    def _create_sized_router[C: Sized](
        sizes: Iterable[int], cls_factory: Callable[[int], type]
    ) -> Callable[[C], C]:
        classes = [cls_factory(i) for i in sizes]

        def router(collection: C) -> C:
            if len(collection) > len(classes):
                return collection

            cls = classes[len(collection)]
            return cls(collection)

        return router

    def __init__(self) -> None:
        ro = list(range(4))
        rw = [1, 1, 2, 3]

        self._seq = self._create_sized_router(ro, lambda i: create_seq_class(i, self.seq))
        self._mut_seq = self._create_sized_router(
            rw, lambda i: create_mut_seq_class(i, self.mut_seq)
        )

        self._set = self._create_sized_router(ro, lambda i: create_set_class(i, self.set))
        self._mut_set = self._create_sized_router(
            rw, lambda i: create_mut_set_class(i, self.mut_set)
        )

        self._mapping = self._create_sized_router(ro, create_mapping_class)
        self._mut_mapping = self._create_sized_router(rw, create_mut_mapping_class)

    def seq[T](self, seq: Sequence[T]) -> Sequence[T]:
        return self._seq(seq)

    def mut_seq[T](self, mut_seq: MutableSequence[T]) -> MutableSequence[T]:
        return self._mut_seq(mut_seq)

    def set[T](self, s: Set[T]) -> Set[T]:
        return self._set(s)

    def mut_set[T](self, mut_set: MutableSet[T]) -> MutableSet[T]:
        return self._mut_set(mut_set)

    def mapping[K, V](self, mapping: Mapping[K, V]) -> Mapping[K, V]:
        return self._mapping(mapping)

    def mut_mapping[K, V](self, mut_mapping: MutableMapping[K, V]) -> MutableMapping[K, V]:
        return self._mut_mapping(mut_mapping)
