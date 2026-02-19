"""Metaclasses for generating optimized set types.

This module implements the set-specific metaclasses that generate immutable Set and MutableSet
implementations with slot-based storage. Elements are stored directly in individual slots.
"""

from itertools import zip_longest
from typing import Any, Optional

from collections.abc import Callable, MutableSet, Sequence, Set

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
    ) -> type:
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

        ns: dict[str, Any] = {"slots": slots}

        if internal_size == 0:
            expansion_ir = ""
        else:
            expansion_ir = "(" + ",".join(f"self.{slots[i]}" for i in range(internal_size)) + ",) = s"

        init_ir = f"""
def __init__(self, s):
    if len(s) != {internal_size}:
        raise ValueError(
            f"Expected provided Set to have exactly {internal_size} elements but it has {{len(s)}}."
        )
    {expansion_ir}
"""
        exec(init_ir, ns)

        contains_ir = f"""
def __contains__(self, value):
    {"\n    ".join(f"if self.{slots[i]} == value: return True" for i in range(internal_size))}
    return False
"""
        exec(contains_ir, ns)

        if internal_size == 0:
            iter_ir = "def __iter__(self): yield from ()"
        else:
            iter_ir = f"""
def __iter__(self):
    {"\n    ".join(f"yield self.{slots[i]}" for i in range(internal_size))}
"""
        exec(iter_ir, ns)

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

        namespace["__init__"] = ns["__init__"]
        namespace["__contains__"] = ns["__contains__"]
        namespace["__iter__"] = ns["__iter__"]
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
    ) -> type:
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

        def _assign(self, s):
            if len(s) > internal_size:
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
            _assign(self, s)

        def __contains__(self, value):
            first = getattr(self, slots[0])
            if isinstance(first, Overflow):
                return value in first.data

            for slot in slots:
                v = getattr(self, slot)
                if v is END:
                    break
                if v == value:
                    return True
            return False

        def __iter__(self):
            yield from OptimizedCollectionMeta._mut_iter(
                self, slots, Overflow, lambda o: o.data, END, lambda v: v
            )

        def __len__(self):
            return OptimizedCollectionMeta._mut_len(
                self, slots, Overflow, lambda o: len(o.data), END
            )

        def add(self, value):
            current = set(self)
            current.add(value)
            _assign(self, current)

        def discard(self, value):
            current = set(self)
            current.discard(value)
            _assign(self, current)

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
