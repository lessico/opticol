from abc import ABCMeta
from collections.abc import Sequence
from itertools import zip_longest
from typing import Any


class OptimizedMappingMeta(ABCMeta):
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        *,
        internal_size: int,
    ) -> type:
        slots = tuple(f"_item{i}" for i in range(internal_size))
        namespace["__slots__"] = slots

        mcs._add_methods(slots, namespace, internal_size)

        return super().__new__(mcs, name, bases, namespace)

    @staticmethod
    def _add_methods(
        item_slots: Sequence[str],
        namespace: dict[str, Any],
        internal_size: int,
    ) -> None:
        if internal_size > 0:
            init_ir = f"""
def __init__(self, {",".join(item_slots)}):
    {"\n    ".join(f"self.{slot} = {slot}" for slot in item_slots)}
"""
            exec(init_ir, namespace)

        def __getitem__(self, key):
            for slot in item_slots:
                item = getattr(self, slot)
                if item[0] == key:
                    return item[1]
            raise KeyError(key)

        def __iter__(self):
            yield from (getattr(self, slot)[0] for slot in item_slots)

        def __len__(_):
            return internal_size

        def __repr__(self):
            items = [
                f"{repr(getattr(self, slot)[0])}: {repr(getattr(self, slot)[1])}"
                for slot in item_slots
            ]
            return f"{{{", ".join(items)}}}"

        namespace["__getitem__"] = __getitem__
        namespace["__iter__"] = __iter__
        namespace["__len__"] = __len__
        namespace["__repr__"] = __repr__


class OptimizedMutableMappingMeta(ABCMeta):
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        *,
        internal_size: int,
    ) -> type:
        if internal_size <= 0:
            raise ValueError(f"{internal_size} is not a valid size for the MutableMapping type.")

        slots = tuple(f"_item{i}" for i in range(internal_size))
        namespace["__slots__"] = slots

        mcs._add_methods(slots, namespace, internal_size)

        return super().__new__(mcs, name, bases, namespace)

    @staticmethod
    def _add_methods(
        item_slots: Sequence[str],
        namespace: dict[str, Any],
        internal_size: int,
    ) -> None:
        def _assign_dict(self, d):
            if len(d) > internal_size:
                setattr(self, item_slots[0], d)
                for slot in item_slots[1:]:
                    setattr(self, slot, None)
            else:
                sentinel = object()
                for pair, slot in zip_longest(d.items(), item_slots, fillvalue=sentinel):
                    if pair is sentinel:
                        setattr(self, slot, None)
                    else:
                        setattr(self, slot, pair)

        def __init__(self, it):
            d = it if isinstance(it, dict) else dict(it)
            _assign_dict(self, d)

        def __getitem__(self, key):
            first = getattr(self, item_slots[0])
            if isinstance(first, dict):
                return first[key]

            for slot in item_slots:
                item = getattr(self, slot)
                if item is None:
                    break

                if item[0] == key:
                    return item[1]

            raise KeyError(key)

        def __setitem__(self, key, value):
            current = dict(self)
            current[key] = value
            _assign_dict(self, current)

        def __delitem__(self, key):
            current = dict(self)
            del current[key]
            _assign_dict(self, current)

        def __iter__(self):
            first = getattr(self, item_slots[0])
            if isinstance(first, dict):
                yield from first
                return

            for slot in item_slots:
                item = getattr(self, slot)
                if item is None:
                    return

                yield item[0]

        def __len__(self):
            first = getattr(self, item_slots[0])
            if isinstance(first, dict):
                return len(first)

            count = 0
            for slot in item_slots:
                if getattr(self, slot) is None:
                    break
                count += 1

            return count

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
