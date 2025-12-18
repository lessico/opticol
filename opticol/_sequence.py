from abc import ABCMeta
from itertools import zip_longest
from typing import Any, Callable

from collections.abc import Sequence

from opticol._sentinel import END, Overflow


def _adjust_index(idx: int, length: int) -> int:
    adjusted = idx if idx >= 0 else length + idx
    if adjusted < 0 or adjusted >= length:
        raise IndexError(f"{adjusted} is outside of the expected bounds.")
    return adjusted


class OptimizedSequenceMeta(ABCMeta):
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        *,
        internal_size: int,
        project: Callable[[list], Sequence],
    ) -> type:
        slots = tuple(f"_item{i}" for i in range(internal_size))
        namespace["__slots__"] = slots

        mcs._add_methods(slots, namespace, internal_size, project)

        return super().__new__(mcs, name, bases, namespace)

    @staticmethod
    def _add_methods(
        item_slots: Sequence[str],
        namespace: dict[str, Any],
        internal_size: int,
        project: Callable[[list], Sequence],
    ) -> None:
        if internal_size > 0:
            init_ir = f"""
def __init__(self, {",".join(item_slots)}):
    {"\n    ".join(f"self.{slot} = {slot}" for slot in item_slots)}
"""
            exec(init_ir, namespace)

        def __getitem__(self, key):
            match key:
                case int():
                    key = _adjust_index(key, len(self))
                    return getattr(self, item_slots[key])
                case slice():
                    indices = range(*key.indices(len(self)))
                    return project([self[i] for i in indices])
                case _:
                    raise TypeError(
                        f"Sequence accessors must be integers or slices, not {type(key)}"
                    )

        def __len__(_):
            return internal_size

        def __repr__(self):
            return f"[{", ".join(repr(getattr(self, slot)) for slot in item_slots)}]"

        namespace["__getitem__"] = __getitem__
        namespace["__len__"] = __len__
        namespace["__repr__"] = __repr__


class OptimizedMutableSequenceMeta(ABCMeta):
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        *,
        internal_size: int,
        project: Callable[[list], Sequence],
    ) -> type:
        if internal_size <= 0:
            raise ValueError(f"{internal_size} is not a valid size for the MutableSequence type.")

        slots = tuple(f"_item{i}" for i in range(internal_size))
        namespace["__slots__"] = slots

        mcs._add_methods(slots, namespace, internal_size, project)

        return super().__new__(mcs, name, bases, namespace)

    @staticmethod
    def _add_methods(
        item_slots: Sequence[str],
        namespace: dict[str, Any],
        internal_size: int,
        project: Callable[[list], Sequence],
    ) -> None:
        def _assign_list(self, l):
            if len(l) > internal_size:
                setattr(self, item_slots[0], Overflow(l))
                for slot in item_slots[1:]:
                    setattr(self, slot, END)
            else:
                sentinel = object()
                for slot, v in zip_longest(item_slots, l, fillvalue=sentinel):
                    if v is sentinel:
                        setattr(self, slot, END)
                    else:
                        setattr(self, slot, v)

        def __init__(self, it):
            collected = it if isinstance(it, list) else list(it)
            _assign_list(self, collected)

        def __getitem__(self, key):
            first = getattr(self, item_slots[0])
            overflowed = isinstance(first, Overflow)

            match key:
                case int():
                    if overflowed:
                        return first.data[key]

                    key = _adjust_index(key, len(self))
                    v = getattr(self, item_slots[key])
                    if v is END:
                        raise IndexError(f"{key} is outside of the expected bounds.")
                    return v
                case slice():
                    if overflowed:
                        return project(first.data[key])

                    indices = range(*key.indices(len(self)))
                    first = getattr(self, item_slots[0])
                    return project([self[i] for i in indices])
                case _:
                    raise TypeError(
                        f"Sequence accessors must be integers or slices, not {type(key)}"
                    )

        def __setitem__(self, key, value):
            current = list(self)
            current[key] = value
            _assign_list(self, current)

        def __delitem__(self, key):
            current = list(self)
            del current[key]
            _assign_list(self, current)

        def __len__(self):
            first = getattr(self, item_slots[0])
            if isinstance(first, Overflow):
                return len(first.data)

            count = 0
            for slot in item_slots:
                if getattr(self, slot) is END:
                    break
                count += 1

            return count

        def insert(self, index, value):
            current = list(self)
            current.insert(index, value)
            _assign_list(self, current)

        def __repr__(self):
            return f"[{", ".join(repr(val) for val in self)}]"

        namespace["__init__"] = __init__
        namespace["__getitem__"] = __getitem__
        namespace["__setitem__"] = __setitem__
        namespace["__delitem__"] = __delitem__
        namespace["__len__"] = __len__
        namespace["insert"] = insert
        namespace["__repr__"] = __repr__
