"""Projector API for pluggable collection optimization strategies.

This module defines the primary consumer-facing API for opticol. Projectors implement a policy
pattern that allows different optimization strategies to be applied to collections. Applications
can use projectors to control how and when collections are optimized for memory efficiency.

The module currently provides three projector implementations:

1. Projector: Abstract base class defining the projector interface. All custom projectors should
   inherit from this class.

2. PassThroughProjector: A no-op projector that returns collections unchanged. Useful for disabling
   optimization or as a base class for selective optimization.

3. OptimizedCollectionProjector: The primary implementation that applies slot-based optimization to
   small collections. This projector routes collections to size-optimized implementations based on
   their length, falling back to standard types for collections outside the configured size range.

Projectors should be used at the API layer or as a DI component which is used to process collection
types in a data model. Then depending on the application configuration and changing necessities,
different optimization schedules can be applied or removed.
"""

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
    """Abstract base class for collection projection strategies.

    Projectors define how collections are transformed or optimized. Each projector must implement
    six methods, one for each collection type (immutable and mutable variants of sequences, sets,
    and mappings).
    """

    @abstractmethod
    def seq[T](self, seq: Sequence[T], /) -> Sequence[T]:
        """Project an immutable sequence.

        Args:
            seq: The sequence to project/optimize.

        Returns:
            A projected sequence (may be the same object or a new optimized instance).
        """

    @abstractmethod
    def mut_seq[T](self, mut_seq: MutableSequence[T], /) -> MutableSequence[T]:
        """Project a mutable sequence.

        Args:
            mut_seq: The mutable sequence to project/optimize.

        Returns:
            A projected mutable sequence.
        """

    @abstractmethod
    def set[T](self, s: Set[T], /) -> Set[T]:
        """Project an immutable set.

        Args:
            s: The set to project/optimize.

        Returns:
            A projected set.
        """

    @abstractmethod
    def mut_set[T](self, mut_set: MutableSet[T], /) -> MutableSet[T]:
        """Project a mutable set.

        Args:
            mut_set: The mutable set to project/optimize.

        Returns:
            A projected mutable set.
        """

    @abstractmethod
    def mapping[K, V](self, mapping: Mapping[K, V], /) -> Mapping[K, V]:
        """Project an immutable mapping.

        Args:
            mapping: The mapping to project/optimize.

        Returns:
            A projected mapping.
        """

    @abstractmethod
    def mut_mapping[K, V](self, mut_mapping: MutableMapping[K, V], /) -> MutableMapping[K, V]:
        """Project a mutable mapping.

        Args:
            mut_mapping: The mutable mapping to project/optimize.

        Returns:
            A projected mutable mapping.
        """


class PassThroughProjector(Projector):
    """Projector that returns all collections unchanged.

    This projector performs no optimization and returns input collections as-is. Useful for
    disabling optimization in specific contexts or as a base class for projectors that selectively
    optimize only certain collection types.
    """

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
    """Primary projector implementation using slot-based optimization for small collections.

    This projector applies memory-efficient slot-based implementations to collections within a
    configured size range. Collections outside this range are returned unchanged as standard Python
    types. The size range is specified at construction time via min_size and max_size parameters.

    For each collection type, the projector pre-generates a set of optimized classes (one for each
    size in the range). When a collection is projected, the projector checks its length and routes
    it to the appropriate size-specific class. If the collection is too large or too small, it's
    returned unchanged.

    The projector also supports recursive optimization: when slicing or using set operations on
    optimized collections, the results are automatically routed back through the projector,
    maintaining optimization for nested structures.
    """

    @staticmethod
    def _create_sized_router[C: Sized](
        min_size: int, max_size: int, cls_factory: Callable[[int], type]
    ) -> Callable[[C], C]:
        """Create a routing function that dispatches collections to size-specific classes.

        Args:
            min_size: Minimum collection size to optimize.
            max_size: Maximum collection size to optimize.
            cls_factory: Factory function that creates optimized classes for a given size.

        Returns:
            A router function that takes a collection and returns either an optimized
            instance or the original collection if outside the size range.
        """
        classes = [cls_factory(size) for size in range(min_size, max_size + 1)]

        def router(collection: C) -> C:
            l = len(collection)
            if l < min_size or l > max_size:
                return collection

            klass = classes[len(collection) - min_size]
            return klass(collection)

        return router

    def __init__(self, min_size: int, max_size: int, recursive: bool) -> None:
        """Initialize the projector with a continuous size range for optimization.

        Sensible ranges for optimization are between 0 and 5.

        Args:
            min_size: Minimum collection size to optimize (inclusive).
            max_size: Maximum collection size to optimize (inclusive).
            recursive: Flag if collection instances created from runtime operations should also be
                optimized via the same projector.
        """
        # Will be either True (if recursive is True) or None (if recursive if False). When *anding*
        # with the possible project function, the result will either be the second argument or None
        # respectively.
        project_guard = recursive or None

        self._seq = self._create_sized_router(
            min_size, max_size, lambda i: create_seq_class(i, project_guard and self.seq)
        )
        self._mut_seq = self._create_sized_router(
            min_size, max_size, lambda i: create_mut_seq_class(i, project_guard and self.mut_seq)
        )

        self._set = self._create_sized_router(
            min_size, max_size, lambda i: create_set_class(i, project_guard and self.set)
        )
        self._mut_set = self._create_sized_router(
            min_size, max_size, lambda i: create_mut_set_class(i, project_guard and self.mut_set)
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
