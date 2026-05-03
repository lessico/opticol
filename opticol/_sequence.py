"""Metaclasses for generating optimized sequence types.

This module implements the sequence-specific metaclasses that generate immutable
Sequence and MutableSequence implementations with slot-based storage.
"""

from typing import Any, Optional

from collections.abc import Callable, MutableSequence, Sequence

from opticol._codegen import def_fn, splice
from opticol._meta import OptimizedCollectionMeta
from opticol._sentinel import END


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

        __init__ = def_fn(f"""
            def __init__(self, seq):
                if len(seq) != {internal_size}:
                    raise ValueError(
                        f"Expected provided Sequence to have exactly {internal_size} elements but "
                        f"it has {{len(seq)}}."
                    )

                {splice(
                    4,
                    [f"self.{slots[i]} = seq[{i}]" for i in range(len(slots))]
                )}""")

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

        _assign = OptimizedCollectionMeta[MutableSequence]._assign(slots, list)
        _mut_state = OptimizedCollectionMeta[MutableSequence]._mut_state(slots)
        _len = OptimizedCollectionMeta[MutableSequence]._len(slots)

        def __init__(self, seq):
            _assign(self, seq, seq, True)

        def __getitem__(self, key):
            overflowed, overflow_data, length = _mut_state(self)

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
            overflowed, overflow_data, length = _mut_state(self)

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
                            _assign(self, overflow_data, overflow_data, False)
                        return

                    current = list(self)
                    current[key] = value
                    _assign(self, current, current, False)
                case _:
                    raise TypeError(
                        f"Sequence accessors must be integers or slices, not {type(key)}"
                    )

        def __delitem__(self, key):
            overflowed, overflow_data, length = _mut_state(self)
            if overflowed:
                del overflow_data[key]
                if len(overflow_data) <= internal_size:
                    _assign(self, overflow_data, overflow_data, False)
                return

            match key:
                case int():
                    adjusted = _adjust_index(key, length)
                    for i, slot in enumerate(slots[adjusted : length - 1], adjusted):
                        next_slot = getattr(self, slots[i + 1])
                        setattr(self, slot, next_slot)

                    if length == internal_size:
                        setattr(self, slots[length - 1], END(length - 1))
                    else:
                        delattr(self, slots[length - 1])
                        getattr(self, slots[internal_size - 1]).length -= 1
                case slice():
                    current = list(self)
                    del current[key]
                    _assign(self, current, current, False)
                case _:
                    raise TypeError(
                        f"Sequence accessors must be integers or slices, not {type(key)}"
                    )

        def insert(self, index, value):
            overflowed, overflow_data, length = _mut_state(self)
            if overflowed:
                overflow_data.insert(index, value)
                return

            if length == internal_size:
                current = list(self)
                current.insert(index, value)
                _assign(self, current, current, False)
                return

            if index >= length:
                setattr(self, slots[length], value)
            else:
                # This behavior matches the python default behavior for wrapping indices on insert,
                # which are different from normal sequence indexing.
                if index < -length:
                    adjusted = 0
                else:
                    adjusted = _adjust_index(index, length)

                for i in range(length, adjusted, -1):
                    prev_slot = getattr(self, slots[i - 1])
                    setattr(self, slots[i], prev_slot)
                setattr(self, slots[adjusted], value)

            if length < internal_size - 1:
                getattr(self, slots[internal_size - 1]).length += 1

        def __repr__(self):
            return f"[{", ".join(repr(val) for val in self)}]"

        namespace["__init__"] = __init__
        namespace["__getitem__"] = __getitem__
        namespace["__setitem__"] = __setitem__
        namespace["__delitem__"] = __delitem__
        namespace["__len__"] = _len
        namespace["insert"] = insert
        namespace["__repr__"] = __repr__
