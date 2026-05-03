"""Metaclasses for generating optimized set types.

This module implements the set-specific metaclasses that generate immutable Set and MutableSet
implementations with slot-based storage. Elements are stored directly in individual slots.
"""

from typing import Any, Optional

from collections.abc import Callable, MutableSet, Sequence, Set

from opticol._codegen import def_fn, guard, spliced
from opticol._meta import OptimizedCollectionMeta
from opticol._sentinel import END


class OptimizedSetMeta(OptimizedCollectionMeta[Set]):
    """Metaclass for generating fixed-size immutable Set implementations.

    Creates Set classes that store exactly the specified number of elements in individual slots.
    Membership testing is performed by linear search. Supports set operations (union, intersection,
    etc.) with optional recursive optimization via the project parameter.

    Because membership testing is done via a linear search, this implementation will accept
    unhashable types. However, it is still not wise to use such values in the set since growing the
    set will likely result in falling back to the python default which will throw.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        *,
        internal_size: int,
        project: Optional[Callable[[Set], Set]],
    ) -> type[Set]:
        return super().__new__(
            mcs,
            name,
            bases,
            namespace,
            internal_size=internal_size,
            project=project,
            collection_name="Set",
        )

    @staticmethod
    def add_methods(
        slots: Sequence[str],
        namespace: dict[str, Any],
        project: Optional[Callable[[Set], Set]],
    ) -> None:
        internal_size = len(slots)

        __init__ = def_fn(f"""
            def __init__(self, s):
                if len(s) != {internal_size}:
                    raise ValueError(
                        "Expected provided Set to have exactly {internal_size} elements but it has "
                        f"{{len(s)}}."
                    )
                {guard(internal_size > 0, f"({",".join(f"self.{slot}" for slot in slots)},) = s")}
            """)

        __contains__ = def_fn(f"""
            def __contains__(self, value):
                return {guard(
                    internal_size > 0,
                    " or ".join(f"self.{slot} == value" for slot in slots), "False")}
            """)

        __iter__ = def_fn(f"""
            def __iter__(self):
                yield from {guard(
                    internal_size > 0,
                    "(" + ", ".join(f"self.{slot}" for slot in slots) + ",)", "()")}
            """)

        def __len__(_):
            return internal_size

        def __repr__(self):
            if internal_size == 0:
                return "set()"
            return f"{{{", ".join(repr(getattr(self, slot)) for slot in slots)}}}"

        if project is not None:

            def _from_iterable(_, it):
                return project(set(it))

        else:

            def _from_iterable(_, it):
                return set(it)

        namespace["_from_iterable"] = classmethod(_from_iterable)

        namespace["__init__"] = __init__
        namespace["__contains__"] = __contains__
        namespace["__iter__"] = __iter__
        namespace["__len__"] = __len__
        namespace["__repr__"] = __repr__


class OptimizedMutableSetMeta(OptimizedCollectionMeta[MutableSet]):
    """Metaclass for generating overflow-capable MutableSet implementations.

    Creates MutableSet classes that use slots for small sets but overflow to a standard set when the
    number of elements exceeds capacity. Supports all standard set operations including add and
    discard. When mutations cause overflow or underflow, the internal representation is
    automatically adjusted between slot-based and set-based storage.

    Because membership testing is done via a linear search, this implementation will accept
    unhashable types. However, it is still not wise to use such values in the set since growing the
    set will likely result in falling back to the python default which will throw.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        *,
        internal_size: int,
        project: Optional[Callable[[MutableSet], MutableSet]],
    ) -> type[MutableSet]:
        return super().__new__(
            mcs,
            name,
            bases,
            namespace,
            internal_size=internal_size or 1,
            project=project,
            collection_name="MutableSet",
        )

    @staticmethod
    def add_methods(
        slots: Sequence[str],
        namespace: dict[str, Any],
        project: Optional[Callable[[MutableSet], MutableSet]],
    ) -> None:
        internal_size = len(slots)

        _assign = OptimizedCollectionMeta[MutableSet]._assign(slots, set)
        _mut_state = OptimizedCollectionMeta[MutableSet]._mut_state(slots)
        _len = OptimizedCollectionMeta[MutableSet]._len(slots)

        def __init__(self, s):
            _assign(self, s, s, True)

        __contains__ = def_fn(
            f"""
            def __contains__(self, value):
                overflowed, data, length = _mut_state(self)
                if overflowed:
                    return value in data
                {spliced(4,
                         [f"if length == {i}: return False\nif self.{slots[i]} == value: return True" for i in range(internal_size)])}
                return False
            """,
            _mut_state=_mut_state,
            slots=slots,
        )

        __iter__ = def_fn(
            f"""
            def __iter__(self):
                overflowed, data, length = _mut_state(self)
                if overflowed:
                    yield from data
                    return

                {spliced(4,
                         [f"if length == {i}: return\nyield self.{slots[i]}" for i in range(internal_size)])}
                for slot in slots[:length]:
                    yield getattr(self, slot)
            """,
            _mut_state=_mut_state,
            slots=slots,
        )

        add = def_fn(
            f"""
            def add(self, value):
                overflowed, data, length = _mut_state(self)
                if overflowed:
                    data.add(value)
                    return

                {spliced(4,
                         [f"if {i} < length and self.{slots[i]} == value: return" for i in range(internal_size)])}

                if length < internal_size:
                    setattr(self, slots[length], value)
                    if length + 1 < internal_size:
                        self.{slots[-1]}.length += 1
                    return

                current = set(self)
                current.add(value)
                _assign(self, current, current, False)
            """,
            _mut_state=_mut_state,
            slots=slots,
            internal_size=internal_size,
            _assign=_assign,
        )

        discard = def_fn(
            f"""
            def discard(self, value):
                overflowed, data, length = _mut_state(self)
                if overflowed:
                    data.discard(value)
                    if len(data) <= internal_size:
                        _assign(self, data, data, False)
                    return

                swap_idx = length - 1
                to_remove_slot_idx = None
                {spliced(4,
                         [f"if {i} < length and self.{slots[i]} == value: to_remove_slot_idx = {i}" for i in range(internal_size)])}

                if to_remove_slot_idx is None:
                    return

                if to_remove_slot_idx != swap_idx:
                    setattr(self, slots[to_remove_slot_idx], getattr(self, slots[swap_idx]))

                if swap_idx < internal_size - 1:
                    delattr(self, slots[swap_idx])

                if swap_idx == internal_size - 1:
                    self.{slots[-1]} = END(length - 1)
                else:
                    self.{slots[-1]}.length -= 1
            """,
            _mut_state=_mut_state,
            slots=slots,
            internal_size=internal_size,
            END=END,
            _assign=_assign,
        )

        def __repr__(self):
            if len(self) == 0:
                return "set()"
            return f"{{{", ".join(repr(val) for val in self)}}}"

        if project is not None:

            def _from_iterable(_, it):
                return project(set(it))

        else:

            def _from_iterable(_, it):
                return set(it)

        namespace["_from_iterable"] = classmethod(_from_iterable)

        namespace["__init__"] = __init__
        namespace["__contains__"] = __contains__
        namespace["__iter__"] = __iter__
        namespace["__len__"] = _len
        namespace["add"] = add
        namespace["discard"] = discard
        namespace["__repr__"] = __repr__
