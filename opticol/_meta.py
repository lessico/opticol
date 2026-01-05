"""Base metaclass for generating optimized slot-based collection types.

This module provides the foundational metaclass used by all optimized collection
implementations. It handles automatic slot generation and provides common helper
methods for mutable collection operations.
"""

from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Iterable, Iterator, Sequence
from typing import Any, Optional


class OptimizedCollectionMeta[C](ABCMeta):
    """Metaclass for creating optimized collection classes with fixed-size slots.

    This metaclass generates collection classes that use __slots__ for memory efficiency. Each
    instance stores elements in individually named slots (_item0, _item1, etc.) based on the
    specified internal_size. Subclasses must implement add_methods() to define collection-specific
    behavior.

    The static helper methods defined here assume that mutable collections follow a standard
    behavior, but otherwise, logic in add_methods can leverage this structure as it sees fit.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        *,
        internal_size: int,
        project: Optional[Callable[[C], C]],
        collection_name: str,
    ) -> type:
        """Create a new optimized collection class with generated slots.

        Args:
            name: The name of the class that will be created.
            bases: Base classes (typically abstract collection types).
            namespace: Class namespace dictionary.
            internal_size: The number of slots for collection items.
            project: Optional projection function for recursive optimization. It is used to project
                the result of operations that create a new collection instance.
            collection_name: Human-readable collection type name for error messages.

        Returns:
            A new optimized collection class using __slots__ with the implementation supplied by
            the subclass.

        Raises:
            ValueError: If internal_size is negative.
        """
        if internal_size < 0:
            raise ValueError(f"{internal_size} is not a valid size for the {collection_name} type.")

        slots = tuple(f"_item{i}" for i in range(internal_size))
        namespace["__slots__"] = slots

        mcs.add_methods(slots, namespace, project)

        return super().__new__(mcs, name, bases, namespace)

    @staticmethod
    @abstractmethod
    def add_methods(
        slots: Sequence[str],
        namespace: dict[str, Any],
        project: Optional[Callable[[C], C]],
    ):
        """Add collection-specific methods to the class namespace.

        Subclasses must implement this to define __init__, __len__, __iter__, and other methods
        required by their respective ABC. Methods are added directly to the namespace dict, which
        will be used to create the class.

        Args:
            slots: Tuple of slot names (_item0, _item1, etc.) for storing elements.
            namespace: Class namespace dict to populate with methods.
            project: Optional projection function for recursive collection optimization.
        """

    @staticmethod
    def _mut_len[O](
        inst: Any,
        slots: Sequence[str],
        overflow_type: type[O],
        overflow_selector: Callable[[O], int],
        end_object: object,
    ) -> int:
        """Calculate length for mutable collections supporting overflow.

        Mutable collections can exceed their allocated slot count, triggering overflow to a standard
        collection type or they may underflow and use sentinel objects to represent absent values.
        This helper assumes the instance follows these conventions and returns its computed length.

        Args:
            inst: The collection instance.
            slots: Slot names to check for elements.
            overflow_type: Type used when collection exceeds slot capacity.
            overflow_selector: Function to extract length from overflow object.
            end_object: Sentinel marking unused slots.

        Returns:
            The number of elements in the collection.
        """
        first = getattr(inst, slots[0])
        if isinstance(first, overflow_type):
            return overflow_selector(first)

        count = 0
        for slot in slots:
            if getattr(inst, slot) is end_object:
                break
            count += 1

        return count

    @staticmethod
    def _mut_iter[O](
        inst: Any,
        slots: Sequence[str],
        overflow_type: type[O],
        overflow_selector: Callable[[O], Iterable],
        end_object: object,
        value_selector: Callable,
    ) -> Iterator:
        """Iterate over elements in mutable collections supporting overflow.

        Similar to _mut_len, this handles iteration for collections that may have overflowed or
        underflowed to different representations.

        Args:
            inst: The collection instance.
            slots: Slot names to iterate over.
            overflow_type: Type used when collection exceeds slot capacity.
            overflow_selector: Function to extract iterable from overflow object.
            end_object: Sentinel marking unused slots.
            value_selector: Function to extract value from slot content.

        Yields:
            Elements from the collection.
        """
        first = getattr(inst, slots[0])
        if isinstance(first, overflow_type):
            yield from overflow_selector(first)
            return

        for slot in slots:
            v = getattr(inst, slot)
            if v is end_object:
                return
            yield value_selector(v)
