"""Metaclasses for generating optimized sequence types.

This module implements the sequence-specific metaclasses that generate immutable
Sequence and MutableSequence implementations with slot-based storage.
"""

from itertools import zip_longest
from typing import Any, Optional

from collections.abc import Callable, MutableSequence, Sequence

from opticol._meta import OptimizedCollectionMeta
from opticol._sentinel import END, Overflow


def _adjust_index(idx: int, length: int) -> int:
    """Normalize a potentially negative index to a positive offset.

    Args:
        idx: The index to normalize (may be negative for reverse indexing).
        length: The length of the sequence being indexed into.

    Returns:
        The normalized positive index.

    Raises:
        IndexError: If the adjusted index is out of bounds.
    """
    adjusted = idx if idx >= 0 else length + idx
    if adjusted < 0 or adjusted >= length:
        raise IndexError(f"{adjusted} is outside of the expected bounds.")
    return adjusted


class OptimizedSequenceMeta(OptimizedCollectionMeta[Sequence]):
    """Metaclass for generating fixed-size immutable Sequence implementations.

    Creates Sequence classes that store exactly the specified number of elements in individual
    slots. Supports indexing (including negative indices) and slicing with optional recursive
    optimization via the project parameter.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        *,
        internal_size: int,
        project: Optional[Callable[[Sequence], Sequence]],
    ) -> type:
        return super().__new__(
            mcs,
            name,
            bases,
            namespace,
            internal_size=internal_size,
            project=project,
            collection_name="Sequence",
        )

    @staticmethod
    def add_methods(
        slots: Sequence[str],
        namespace: dict[str, Any],
        project: Optional[Callable[[Sequence], Sequence]],
    ) -> None:
        internal_size = len(slots)

        def __init__(self, seq):
            if len(seq) != internal_size:
                raise ValueError(
                    f"Expected provided Sequence to have exactly {internal_size} elements but it "
                    f"has {len(seq)}."
                )

            for slot, v in zip(slots, seq, strict=True):
                setattr(self, slot, v)

        def __getitem__(self, key):
            match key:
                case int():
                    key = _adjust_index(key, len(self))
                    return getattr(self, slots[key])
                case slice():
                    indices = range(*key.indices(len(self)))
                    base = [self[i] for i in indices]
                    if project is None:
                        return base

                    return project(base)
                case _:
                    raise TypeError(
                        f"Sequence accessors must be integers or slices, not {type(key)}"
                    )

        def __len__(_):
            return internal_size

        def __repr__(self):
            return f"[{", ".join(repr(getattr(self, slot)) for slot in slots)}]"

        namespace["__init__"] = __init__
        namespace["__getitem__"] = __getitem__
        namespace["__len__"] = __len__
        namespace["__repr__"] = __repr__


class OptimizedMutableSequenceMeta(OptimizedCollectionMeta[MutableSequence]):
    """Metaclass for generating overflow-capable MutableSequence implementations.

    Creates MutableSequence classes that use slots for small collections but overflow to a standard
    list when the number of elements exceeds capacity. Supports all standard list operations
    including indexing, slicing, insertion, and deletion. When mutations cause overflow or
    underflow, the internal representation is automatically adjusted.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        *,
        internal_size: int,
        project: Optional[Callable[[MutableSequence], MutableSequence]],
    ) -> type:
        return super().__new__(
            mcs,
            name,
            bases,
            namespace,
            internal_size=internal_size or 1,
            project=project,
            collection_name="MutableSequence",
        )

    @staticmethod
    def add_methods(
        slots: Sequence[str],
        namespace: dict[str, Any],
        project: Optional[Callable[[MutableSequence], MutableSequence]],
    ) -> None:
        internal_size = len(slots)

        def _assign(self, seq):
            if len(seq) > internal_size:
                setattr(self, slots[0], Overflow(seq))
                for slot in slots[1:]:
                    setattr(self, slot, END)
            else:
                sentinel = object()
                for slot, v in zip_longest(slots, seq, fillvalue=sentinel):
                    if v is sentinel:
                        setattr(self, slot, END)
                    else:
                        setattr(self, slot, v)

        def __init__(self, seq):
            _assign(self, seq)

        def __getitem__(self, key):
            first = getattr(self, slots[0])
            overflowed = isinstance(first, Overflow)

            match key:
                case int():
                    if overflowed:
                        return first.data[key]

                    key = _adjust_index(key, len(self))
                    v = getattr(self, slots[key])
                    if v is END:
                        raise IndexError(f"{key} is outside of the expected bounds.")
                    return v
                case slice():
                    if overflowed:
                        base = first.data[key]
                    else:
                        indices = range(*key.indices(len(self)))
                        first = getattr(self, slots[0])
                        base = [self[i] for i in indices]

                    if project is None:
                        return base

                    return project(base)
                case _:
                    raise TypeError(
                        f"Sequence accessors must be integers or slices, not {type(key)}"
                    )

        def __setitem__(self, key, value):
            current = list(self)
            current[key] = value
            _assign(self, current)

        def __delitem__(self, key):
            current = list(self)
            del current[key]
            _assign(self, current)

        def __len__(self):
            return OptimizedCollectionMeta._mut_len(
                self, slots, Overflow, lambda o: len(o.data), END
            )

        def insert(self, index, value):
            current = list(self)
            current.insert(index, value)
            _assign(self, current)

        def __repr__(self):
            return f"[{", ".join(repr(val) for val in self)}]"

        namespace["__init__"] = __init__
        namespace["__getitem__"] = __getitem__
        namespace["__setitem__"] = __setitem__
        namespace["__delitem__"] = __delitem__
        namespace["__len__"] = __len__
        namespace["insert"] = insert
        namespace["__repr__"] = __repr__
