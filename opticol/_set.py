"""Metaclasses for generating optimized set types.

This module implements the set-specific metaclasses that generate immutable Set and MutableSet
implementations with slot-based storage. Elements are stored directly in individual slots.
"""

from itertools import zip_longest
from typing import Any, Optional

from collections.abc import Callable, MutableSet, Sequence, Set

from opticol._codegen import def_fn, guard, rootit, spliced
from opticol._meta import OptimizedCollectionMeta
from opticol._sentinel import END, Overflow


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

        __init__ = def_fn(rootit(f"""
            def __init__(self, s):
                if len(s) != {internal_size}:
                    raise ValueError(
                        "Expected provided Set to have exactly {internal_size} elements but it has "
                        f"{{len(s)}}."
                    )
                {guard(internal_size > 0, f"({",".join(f"self.{slot}" for slot in slots)},) = s")}
            """))

        __contains__ = def_fn(rootit(f"""
            def __contains__(self, value):
                return {guard(
                    internal_size > 0,
                    " or ".join(f"self.{slot} == value" for slot in slots), "False")}
            """))

        __iter__ = def_fn(rootit(f"""
            def __iter__(self):
                yield from {guard(
                    internal_size > 0,
                    "(" + ", ".join(f"self.{slot}" for slot in slots) + ",)", "()")}
            """))

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

        def _assign(self, s, from_outside):
            if len(s) > internal_size:
                if from_outside:
                    s = set(s)
                setattr(self, slots[0], Overflow(s))
                for slot in slots[1:]:
                    setattr(self, slot, END)
            else:
                sentinel = object()
                for slot, v in zip_longest(slots, s, fillvalue=sentinel):
                    if v is sentinel:
                        setattr(self, slot, END)
                    else:
                        setattr(self, slot, v)

        def __init__(self, s):
            _assign(self, s, True)

        __contains__ = def_fn(
            rootit(f"""
            def __contains__(self, value):
                first = self.{slots[0]}
                if isinstance(first, Overflow):
                    return value in first.data
                {spliced(4, [rootit(f"""
                            if self.{slot} is END: return False
                            if self.{slot} == value: return True""") for slot in slots])}
                return False
            """),
            Overflow=Overflow,
            END=END,
        )

        __iter__ = OptimizedCollectionMeta[MutableSet]._mut_iter(
            slots, Overflow, lambda o: o.data, END, lambda v: v
        )

        __len__ = OptimizedCollectionMeta[MutableSet]._mut_len(
            slots, Overflow, lambda o: len(o.data), END
        )

        def add(self, value):
            # If the set is overflowed, then just add directly to the overflow buffer.
            first = getattr(self, slots[0])
            if isinstance(first, Overflow):
                first.data.add(value)
                return

            # If the set state is managed on the slots, then check if the item has to be added at
            # all before continuing.
            for item in self:
                if value == item:
                    return

            # If not in overflow, check if there are any extra slots to put the new value in.
            last = getattr(self, slots[-1])
            if last is END:
                idx = len(self)
                setattr(self, slots[idx], value)
                return

            # Otherwise there are no extra slots, and the store just has to be reassigned.
            current = set(self)
            current.add(value)
            _assign(self, current, False)
            return

        def discard(self, value):
            # If the set is overflowed, then try to remove the item and check if the storage type
            # needs to change.
            first = getattr(self, slots[0])
            if isinstance(first, Overflow):
                first.data.discard(value)
                if len(first.data) <= internal_size:
                    _assign(self, first.data, False)
                return

            # Otherwise, loop through to find the item and then swap with the last item.
            swap_idx = len(slots) - 1
            to_remove_slot_idx = None
            for i, slot in enumerate(slots):
                item = getattr(self, slot)
                if item is END:
                    swap_idx = i - 1
                    break

                if item == value:
                    to_remove_slot_idx = i

            if to_remove_slot_idx is not None:
                if to_remove_slot_idx == swap_idx:
                    setattr(self, slots[to_remove_slot_idx], END)
                else:
                    swap_value = getattr(self, slots[swap_idx])
                    setattr(self, slots[to_remove_slot_idx], swap_value)
                    setattr(self, slots[swap_idx], END)

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
        namespace["__len__"] = __len__
        namespace["add"] = add
        namespace["discard"] = discard
        namespace["__repr__"] = __repr__
