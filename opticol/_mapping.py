"""Metaclasses for generating optimized mapping types.

This module implements the mapping-specific metaclasses that generate immutable Mapping and
MutableMapping implementations with slot-based storage. Each key-value pair is stored as a tuple in
an individual slot.
"""

from collections.abc import Callable, Mapping, MutableMapping, Sequence
from typing import Any, Optional

from opticol._codegen import def_fn, guard, spliced
from opticol._meta import OptimizedCollectionMeta
from opticol._sentinel import END


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

        __init__ = def_fn(f"""
            def __init__(self, mapping):
                if len(mapping) != {internal_size}:
                    raise ValueError(
                        "Expected provided Mapping to have exactly {internal_size} elements but it "
                        f"has {{len(mapping)}}."
                    )
                {guard(
                    internal_size > 0,
                    f"({",".join(f"self.{slot}" for slot in slots)},) = mapping.items()")}
            """)

        __getitem__ = def_fn(f"""
            def __getitem__(self, key):
                {spliced(4, [f"if self.{slot}[0] == key: return self.{slot}[1]" for slot in slots])}
                raise KeyError(key)
            """)

        __iter__ = def_fn(f"""
            def __iter__(self):
                yield from {guard(
                    internal_size > 0,
                    "(" + ", ".join(f"self.{slot}[0]" for slot in slots) + ",)", "()")}
            """)

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

        _assign = OptimizedCollectionMeta[MutableMapping]._assign(slots, dict)
        _mut_state = OptimizedCollectionMeta[MutableMapping]._mut_state(slots)
        _len = OptimizedCollectionMeta[MutableMapping]._len(slots)

        def __init__(self, mapping):
            _assign(self, mapping, mapping.items(), True)

        __getitem__ = def_fn(
            f"""
            def __getitem__(self, key):
                overflowed, data, length = _mut_state(self)
                if overflowed:
                    return data[key]

                {spliced(
                    4,
                    [f"""
                    if {i} >= length: raise KeyError(key)
                    item = self.{slot}
                    if item[0] == key: return item[1]""" for i, slot in enumerate(slots)])}

                raise KeyError(key)""",
            _mut_state=_mut_state,
            KeyError=KeyError,
        )

        def __setitem__(self, key, value):
            overflowed, data, length = _mut_state(self)
            if overflowed:
                data[key] = value
                return

            for slot in slots[:length]:
                tup = getattr(self, slot)
                if tup[0] == key:
                    setattr(self, slot, (tup[0], value))
                    return

            if length < internal_size:
                tup = (key, value)
                setattr(self, slots[length], tup)
                if length < internal_size - 1:
                    getattr(self, slots[-1]).length += 1

            current = dict(self)
            current[key] = value
            _assign(self, current, current.items(), False)

        def __delitem__(self, key):
            # If the mapping is in an overflowed representation then call the normal dict logic and
            # check if the number of elements can be assigned back to slot based representation.
            overflowed, data, length = _mut_state(self)
            if overflowed:
                del data[key]
                if length - 1 <= internal_size:
                    _assign(self, data, data.items(), False)
                return

            # Otherwise, try to find the location of the key.
            to_remove_idx = -1
            for i, slot in enumerate(slots[:length]):
                tup = getattr(self, slot)
                if tup[0] == key:
                    to_remove_idx = i
                    break

            if to_remove_idx < 0:
                raise KeyError(key)

            if to_remove_idx != length - 1:
                setattr(self, slots[to_remove_idx], getattr(self, slots[length - 1]))

            if length == internal_size:
                setattr(self, slots[-1], END(length - 1))
            else:
                delattr(self, slots[length - 1])
                getattr(self, slots[-1]).length -= 1

        def __iter__(self):
            overflowed, data, length = _mut_state(self)
            if overflowed:
                yield from data
                return
            for slot in slots[:length]:
                yield getattr(self, slot)[0]

        def popitem(self):
            overflowed, data, length = _mut_state(self)
            if overflowed:
                item = data.popitem()
                if len(data) <= internal_size:
                    _assign(self, data, data.items(), False)
                return item

            if length == 0:
                raise KeyError

            last = getattr(self, slots[length - 1])
            if length == internal_size:
                setattr(self, slots[-1], END(length - 1))
                return last

            end = getattr(self, slots[-1])
            end.length -= 1
            return last

        def __repr__(self):
            items = [f"{repr(k)}: {repr(v)}" for k, v in self.items()]
            return f"{{{", ".join(items)}}}"

        namespace["__init__"] = __init__
        namespace["__getitem__"] = __getitem__
        namespace["__setitem__"] = __setitem__
        namespace["__delitem__"] = __delitem__
        namespace["__iter__"] = __iter__
        namespace["__len__"] = _len
        namespace["__repr__"] = __repr__

        # Override mixin popitem to match dict's LIFO ordering. Although it's not a requirement of
        # a MutableMapping instance to match this, the ideal case is for this to be an exact
        # in-place replacement for dict.
        namespace["popitem"] = popitem
