"""Metaclasses for generating optimized sequence types.

This module implements the sequence-specific metaclasses that generate immutable
Sequence and MutableSequence implementations with slot-based storage.
"""

from typing import Any, Optional

from collections.abc import Callable, MutableSequence, Sequence

from opticol._meta import OptimizedCollectionMeta
from opticol._sentinel import ENDWithLength, Overflow


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
    ) -> type[Sequence]:
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
    ) -> type[MutableSequence]:
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

        def _assign(self, seq, from_outside):
            length = len(seq)
            if length > internal_size:
                if from_outside:
                    seq = list(seq)

                setattr(self, slots[0], Overflow(seq))
                for slot in slots[1:-1]:
                    try:
                        delattr(self, slot)
                    except AttributeError:
                        break
                if internal_size > 1:
                    setattr(self, slots[-1], ENDWithLength(-1))
            else:
                for slot, v in zip(slots, seq):
                    setattr(self, slot, v)
                for slot in slots[length:-1]:
                    try:
                        delattr(self, slot)
                    except AttributeError:
                        break
                if length < internal_size:
                    setattr(self, slots[-1], ENDWithLength(length))

        def _overflow_state(self) -> tuple[bool, Optional[list], int]:
            last = getattr(self, slots[-1])
            if isinstance(last, ENDWithLength):
                inline_length = last.length
                if inline_length < 0:
                    l = getattr(self, slots[0]).data
                    return True, l, len(l)
                return False, None, inline_length
            if isinstance(last, Overflow):
                l = last.data
                return True, l, len(l)
            return False, None, internal_size

        def __init__(self, seq):
            _assign(self, seq, True)

        def __getitem__(self, key):
            overflowed, overflow_data, length = _overflow_state(self)

            match key:
                case int():
                    if overflowed:
                        return overflow_data[key]

                    adjusted = _adjust_index(key, length)
                    return getattr(self, slots[adjusted])
                case slice():
                    if overflowed:
                        base = overflow_data[key]
                    else:
                        indices = range(*key.indices(length))
                        base = [getattr(self, slots[i]) for i in indices]

                    if project is None:
                        return base

                    return project(base)
                case _:
                    raise TypeError(
                        f"Sequence accessors must be integers or slices, not {type(key)}"
                    )

        def __setitem__(self, key, value):
            overflowed, overflow_data, length = _overflow_state(self)

            match key:
                case int():
                    if overflowed:
                        overflow_data[key] = value
                        return

                    adjusted = _adjust_index(key, length)
                    setattr(self, slots[adjusted], value)
                case slice():
                    if overflowed:
                        overflow_data[key] = value
                        if length <= internal_size:
                            _assign(self, overflow_data, False)
                        return

                    current = list(self)
                    current[key] = value
                    _assign(self, current, False)
                case _:
                    raise TypeError(
                        f"Sequence accessors must be integers or slices, not {type(key)}"
                    )

        def __delitem__(self, key):
            current = list(self)
            del current[key]
            _assign(self, current, False)

        def __len__(self) -> int:
            _, _, length = _overflow_state(self)
            return length

        def insert(self, index, value):
            current = list(self)
            current.insert(index, value)
            _assign(self, current, False)

        def __repr__(self):
            return f"[{", ".join(repr(val) for val in self)}]"

        namespace["__init__"] = __init__
        namespace["__getitem__"] = __getitem__
        namespace["__setitem__"] = __setitem__
        namespace["__delitem__"] = __delitem__
        namespace["__len__"] = __len__
        namespace["insert"] = insert
        namespace["__repr__"] = __repr__
