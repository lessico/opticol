"""Base metaclass for generating optimized slot-based collection types.

This module provides the foundational metaclass used by all optimized collection
implementations. It handles automatic slot generation and provides common helper
methods for mutable collection operations.
"""

from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Iterable, Sequence
from typing import Any, Optional

from opticol._codegen import def_fn
from opticol._sentinel import END, Overflow


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
    ) -> type[C]:
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

        return super().__new__(mcs, name, bases, namespace)  # type: ignore[return-value]

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
    def _assign(
        slots: Sequence[str], ctor: Callable[[C], C]
    ) -> Callable[[C, C, Iterable, bool], None]:
        return def_fn(
            f"""
            def _assign(self, collection, iterable, from_outside):
                length = len(collection)
                if length > internal_size:
                    if from_outside:
                        collection = ctor(collection)

                    self.{slots[0]} = Overflow(collection)
                    for slot in slots[1:-1]:
                        try:
                            delattr(self, slot)
                        except AttributeError:
                            break
                    if internal_size > 1:
                        self.{slots[-1]} = END(-1)
                else:
                    for slot, v in zip(slots, iterable):
                        setattr(self, slot, v)
                    for slot in slots[length:-1]:
                        try:
                            delattr(self, slot)
                        except AttributeError:
                            break
                    if length < internal_size:
                        self.{slots[-1]} = END(length)""",
            internal_size=len(slots),
            slots=slots,
            ctor=ctor,
            Overflow=Overflow,
            END=END,
            zip=zip,
            AttributeError=AttributeError,
        )

    @staticmethod
    def _mut_state(slots: Sequence[str]) -> Callable[[C], tuple[bool, Optional[C], int]]:
        return def_fn(
            f"""
            def _mut_state(self):
                last = self.{slots[-1]}
                if isinstance(last, END):
                    inline_length = last.length
                    if inline_length < 0:
                        l = self.{slots[0]}.data
                        return True, l, len(l)
                    return False, None, inline_length
                if isinstance(last, Overflow):
                    l = last.data
                    return True, l, len(l)
                return False, None, internal_size""",
            internal_size=len(slots),
            END=END,
            Overflow=Overflow,
        )

    @staticmethod
    def _len(slots: Sequence[str]) -> Callable[[C], int]:
        return def_fn(
            f"""
            def _len(self):
                last = self.{slots[-1]}
                if isinstance(last, END):
                    inline_length = last.length
                    if inline_length < 0:
                        l = self.{slots[0]}.data
                        return len(l)
                    return inline_length
                if isinstance(last, Overflow):
                    l = last.data
                    return len(l)
                return internal_size""",
            internal_size=len(slots),
            END=END,
            Overflow=Overflow,
        )
