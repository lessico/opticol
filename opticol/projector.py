from abc import ABC, abstractmethod
from collections.abc import (
    Callable,
    Sized,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Set,
)

from opticol.factory import (
    create_mapping_class,
    create_mut_mapping_class,
    create_mut_seq_class,
    create_mut_set_class,
    create_seq_class,
    create_set_class,
)


class Projector(ABC):
    @abstractmethod
    def seq[T](self, seq: Sequence[T], /) -> Sequence[T]: ...

    @abstractmethod
    def mut_seq[T](self, mut_seq: MutableSequence[T], /) -> MutableSequence[T]: ...

    @abstractmethod
    def set[T](self, s: Set[T], /) -> Set[T]: ...

    @abstractmethod
    def mut_set[T](self, mut_set: MutableSet[T], /) -> MutableSet[T]: ...

    @abstractmethod
    def mapping[K, V](self, mapping: Mapping[K, V], /) -> Mapping[K, V]: ...

    @abstractmethod
    def mut_mapping[K, V](self, mut_mapping: MutableMapping[K, V], /) -> MutableMapping[K, V]: ...


class PassThroughProjector(ABC):
    def seq[T](self, seq: Sequence[T], /) -> Sequence[T]:
        return seq

    def mut_seq[T](self, mut_seq: MutableSequence[T], /) -> MutableSequence[T]:
        return mut_seq

    def set[T](self, s: Set[T], /) -> Set[T]:
        return s

    def mut_set[T](self, mut_set: MutableSet[T], /) -> MutableSet[T]:
        return mut_set

    def mapping[K, V](self, mapping: Mapping[K, V], /) -> Mapping[K, V]:
        return mapping

    def mut_mapping[K, V](self, mut_mapping: MutableMapping[K, V], /) -> MutableMapping[K, V]:
        return mut_mapping


class OptimizedCollectionProjector(Projector):
    @staticmethod
    def _create_sized_router[C: Sized](
        min_size: int, max_size: int, cls_factory: Callable[[int], type]
    ) -> Callable[[C], C]:
        classes = [cls_factory(size) for size in range(min_size, max_size + 1)]

        def router(collection: C) -> C:
            l = len(collection)
            if l < min_size or l > max_size:
                return collection

            klass = classes[len(collection) - min_size]
            return klass(collection)

        return router

    def __init__(self, *, min_size: int = 0, max_size: int = 3) -> None:
        self._seq = self._create_sized_router(
            min_size, max_size, lambda i: create_seq_class(i, self.seq)
        )
        self._mut_seq = self._create_sized_router(
            min_size, max_size, lambda i: create_mut_seq_class(i, self.mut_seq)
        )

        self._set = self._create_sized_router(
            min_size, max_size, lambda i: create_set_class(i, self.set)
        )
        self._mut_set = self._create_sized_router(
            min_size, max_size, lambda i: create_mut_set_class(i, self.mut_set)
        )

        self._mapping = self._create_sized_router(min_size, max_size, create_mapping_class)
        self._mut_mapping = self._create_sized_router(min_size, max_size, create_mut_mapping_class)

    def seq[T](self, seq: Sequence[T], /) -> Sequence[T]:
        return self._seq(seq)

    def mut_seq[T](self, mut_seq: MutableSequence[T], /) -> MutableSequence[T]:
        return self._mut_seq(mut_seq)

    def set[T](self, s: Set[T], /) -> Set[T]:
        return self._set(s)

    def mut_set[T](self, mut_set: MutableSet[T], /) -> MutableSet[T]:
        return self._mut_set(mut_set)

    def mapping[K, V](self, mapping: Mapping[K, V], /) -> Mapping[K, V]:
        return self._mapping(mapping)

    def mut_mapping[K, V](self, mut_mapping: MutableMapping[K, V], /) -> MutableMapping[K, V]:
        return self._mut_mapping(mut_mapping)
