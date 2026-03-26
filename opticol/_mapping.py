"""Metaclasses for generating optimized mapping types.

This module implements the mapping-specific metaclasses that generate immutable Mapping and
MutableMapping implementations with slot-based storage. Each key-value pair is stored as a tuple in
an individual slot.
"""

from collections.abc import Callable, Mapping, MutableMapping, Sequence
from itertools import zip_longest
import operator
from typing import Any, Optional

from opticol._codegen import def_fn, guard, rootit, spliced
from opticol._meta import OptimizedCollectionMeta


class OptimizedMappingMeta(OptimizedCollectionMeta[Mapping]):
    """Metaclass for generating fixed-size immutable Mapping implementations.

    Creates Mapping classes that store exactly the specified number of key-value pairs in individual
    slots. Each slot contains a (key, value) tuple. Lookups are performed by linear search through
    the slots.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        *,
        internal_size: int,
    ) -> type[Mapping]:
        return super().__new__(
            mcs,
            name,
            bases,
            namespace,
            internal_size=internal_size,
            project=None,
            collection_name="Mapping",
        )

    @staticmethod
    def add_methods(
        slots: Sequence[str],
        namespace: dict[str, Any],
        _: Optional[Callable[[Mapping], Mapping]],
    ) -> None:
        internal_size = len(slots)

        __init__ = def_fn(rootit(f"""
            def __init__(self, mapping):
                if len(mapping) != {internal_size}:
                    raise ValueError(
                        "Expected provided Mapping to have exactly {internal_size} elements but it "
                        f"has {{len(mapping)}}."
                    )
                {guard(internal_size > 0, f"({",".join(f"self.{slot}" for slot in slots)},) = mapping.items()")}
            """))

        __getitem__ = def_fn(rootit(f"""
            def __getitem__(self, key):
                {spliced(4, [f"if self.{slot}[0] == key: return self.{slot}[1]" for slot in slots])}
                raise KeyError(key)
            """))

        __iter__ = def_fn(rootit(f"""
            def __iter__(self):
                yield from {guard(internal_size > 0, "(" + ", ".join(f"self.{slot}[0]" for slot in slots) + ",)", "()")}
            """))

        def __len__(_):
            return internal_size

        def __repr__(self):
            items = [
                f"{repr(getattr(self, slot)[0])}: {repr(getattr(self, slot)[1])}" for slot in slots
            ]
            return f"{{{", ".join(items)}}}"

        namespace["__init__"] = __init__
        namespace["__getitem__"] = __getitem__
        namespace["__iter__"] = __iter__
        namespace["__len__"] = __len__
        namespace["__repr__"] = __repr__


class OptimizedMutableMappingMeta(OptimizedCollectionMeta[MutableMapping]):
    """Metaclass for generating overflow-capable MutableMapping implementations.

    Creates MutableMapping classes that use slots for small mappings but overflow to a standard dict
    when the number of key-value pairs exceeds capacity. Supports all standard dict operations. When
    mutations cause overflow or underflow, the internal representation is automatically adjusted.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        *,
        internal_size: int,
    ) -> type[MutableMapping]:
        return super().__new__(
            mcs,
            name,
            bases,
            namespace,
            internal_size=internal_size or 1,
            project=None,
            collection_name="MutableMapping",
        )

    @staticmethod
    def add_methods(
        slots: Sequence[str],
        namespace: dict[str, Any],
        _: Optional[Callable[[MutableMapping], MutableMapping]],
    ) -> None:
        internal_size = len(slots)

        def _assign(self, mapping, from_outside):
            if len(mapping) > internal_size:
                if from_outside:
                    mapping = dict(mapping)
                setattr(self, slots[0], mapping)
                for slot in slots[1:]:
                    setattr(self, slot, None)
            else:
                sentinel = object()
                for pair, slot in zip_longest(mapping.items(), slots, fillvalue=sentinel):
                    if pair is sentinel:
                        setattr(self, slot, None)
                    else:
                        setattr(self, slot, pair)

        def __init__(self, mapping):
            _assign(self, mapping, True)

        def __getitem__(self, key):
            first = getattr(self, slots[0])
            if isinstance(first, dict):
                return first[key]

            for slot in slots:
                item = getattr(self, slot)
                if item is None:
                    break

                if item[0] == key:
                    return item[1]

            raise KeyError(key)

        def __setitem__(self, key, value):
            current = dict(self)
            current[key] = value
            _assign(self, current, False)

        def __delitem__(self, key):
            current = dict(self)
            del current[key]
            _assign(self, current, False)

        __iter__ = OptimizedCollectionMeta[MutableMapping]._mut_iter(slots, dict, lambda d: d, None, operator.itemgetter(0))

        __len__ = OptimizedCollectionMeta[MutableMapping]._mut_len(slots, dict, len, None)

        def popitem(self):
            first = getattr(self, slots[0])
            if isinstance(first, dict):
                return first.popitem()

            # Walk backward through slots to find the last non-empty slot (LIFO order)
            for slot in reversed(slots):
                item = getattr(self, slot)
                if item is not None:
                    setattr(self, slot, None)
                    return item

            raise KeyError

        def __repr__(self):
            items = [f"{repr(k)}: {repr(v)}" for k, v in self.items()]
            return f"{{{", ".join(items)}}}"

        namespace["__init__"] = __init__
        namespace["__getitem__"] = __getitem__
        namespace["__setitem__"] = __setitem__
        namespace["__delitem__"] = __delitem__
        namespace["__iter__"] = __iter__
        namespace["__len__"] = __len__
        namespace["__repr__"] = __repr__

        # Override mixin popitem to match dict's LIFO ordering. Although it's not a requirement of
        # a MutableMapping instance to match this, the ideal case is for this to be an exact
        # in-place replacement for dict.
        namespace["popitem"] = popitem
