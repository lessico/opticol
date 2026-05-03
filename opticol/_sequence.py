"""Metaclasses for generating optimized sequence types.

This module implements the sequence-specific metaclasses that generate immutable
Sequence and MutableSequence implementations with slot-based storage.
"""

from typing import Any, Optional

from collections.abc import Callable, MutableSequence, Sequence

from opticol._codegen import def_fn, guard, rootit, splice
from opticol._meta import OptimizedCollectionMeta
from opticol._sentinel import END


def _adjust_index_snippet(idx_var: str, length_var: str, result_var: str) -> str:
    return rootit(f"""
        {result_var} = {idx_var} if {idx_var} >= 0 else {length_var} + {idx_var}
        if {result_var} < 0 or {result_var} >= {length_var}:
            raise IndexError(f"{{{result_var}}} is outside of the expected bounds.")
        """)


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

        __getitem__ = def_fn(
            f"""
            def __getitem__(self, key):
                overflowed, overflow_data, length = _mut_state(self)

                match key:
                    case int():
                        if overflowed:
                            return overflow_data[key]

                        {splice(6, [_adjust_index_snippet("key", "length", "adjusted")])}
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
                            f"Sequence accessors must be integers or slices, not {{type(key)}}"
                        )
            """,
            _mut_state=_mut_state,
            slots=slots,
            project=project,
            IndexError=IndexError,
        )

        __setitem__ = def_fn(
            f"""
            def __setitem__(self, key, value):
                overflowed, overflow_data, length = _mut_state(self)

                match key:
                    case int():
                        if overflowed:
                            overflow_data[key] = value
                            return

                        {splice(6, [_adjust_index_snippet("key", "length", "adjusted")])}
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
                            f"Sequence accessors must be integers or slices, not {{type(key)}}"
                        )
            """,
            _mut_state=_mut_state,
            slots=slots,
            internal_size=internal_size,
            _assign=_assign,
            IndexError=IndexError,
        )

        __delitem__ = def_fn(
            f"""
            def __delitem__(self, key):
                overflowed, overflow_data, length = _mut_state(self)
                if overflowed:
                    del overflow_data[key]
                    if len(overflow_data) <= internal_size:
                        _assign(self, overflow_data, overflow_data, False)
                    return

                match key:
                    case int():
                        {splice(6, [_adjust_index_snippet("key", "length", "adjusted")])}
                        {guard(internal_size > 1, splice(6, [
                            f"if {i} >= adjusted and {i} < length - 1: self.{slots[i]} = self.{slots[i + 1]}"
                            for i in range(internal_size - 1)
                        ]))}

                        if length == internal_size:
                            self.{slots[-1]} = END(length - 1)
                        else:
                            delattr(self, slots[length - 1])
                            self.{slots[-1]}.length -= 1
                    case slice():
                        current = list(self)
                        del current[key]
                        _assign(self, current, current, False)
                    case _:
                        raise TypeError(
                            f"Sequence accessors must be integers or slices, not {{type(key)}}"
                        )
            """,
            _mut_state=_mut_state,
            slots=slots,
            internal_size=internal_size,
            _assign=_assign,
            END=END,
            IndexError=IndexError,
        )

        insert = def_fn(
            f"""
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
                    if index < -length:
                        adjusted = 0
                    else:
                        {splice(6, [_adjust_index_snippet("index", "length", "adjusted")])}
                    {guard(internal_size > 1, splice(5, [
                        f"if {i} > adjusted and {i} <= length: self.{slots[i]} = self.{slots[i - 1]}"
                        for i in range(internal_size - 1, 0, -1)
                    ]))}
                    setattr(self, slots[adjusted], value)

                if length + 1 < internal_size:
                    self.{slots[-1]}.length += 1
            """,
            _mut_state=_mut_state,
            slots=slots,
            internal_size=internal_size,
            _assign=_assign,
            IndexError=IndexError,
        )

        def __repr__(self):
            return f"[{", ".join(repr(val) for val in self)}]"

        namespace["__init__"] = __init__
        namespace["__getitem__"] = __getitem__
        namespace["__setitem__"] = __setitem__
        namespace["__delitem__"] = __delitem__
        namespace["__len__"] = _len
        namespace["insert"] = insert
        namespace["__repr__"] = __repr__
