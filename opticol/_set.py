from abc import ABCMeta
from itertools import zip_longest
from typing import Any, Callable

from collections.abc import Sequence, Set

from opticol._sentinel import END, Overflow


class OptimizedSetMeta(ABCMeta):
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        *,
        internal_size: int,
        project: Callable[[set], Set],
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
        project: Callable[[set], Set],
    ) -> None:
        if internal_size > 0:
            init_ir = f"""
def __init__(self, {",".join(item_slots)}):
    {"\n    ".join(f"self.{slot} = {slot}" for slot in item_slots)}
"""
            exec(init_ir, namespace)

        def __contains__(self, value):
            for slot in item_slots:
                if getattr(self, slot) == value:
                    return True
            return False

        def __iter__(self):
            for slot in item_slots:
                yield getattr(self, slot)

        def __len__(_):
            return internal_size

        def __repr__(self):
            if internal_size == 0:
                return "set()"
            return f"{{{", ".join(repr(getattr(self, slot)) for slot in item_slots)}}}"

        def _from_iterable(_, it):
            return project(set(it))

        namespace["__contains__"] = __contains__
        namespace["__iter__"] = __iter__
        namespace["__len__"] = __len__
        namespace["__repr__"] = __repr__
        namespace["_from_iterable"] = classmethod(_from_iterable)


class OptimizedMutableSetMeta(ABCMeta):
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        *,
        internal_size: int,
        project: Callable[[set], Set],
    ) -> type:
        if internal_size <= 0:
            raise ValueError(f"{internal_size} is not a valid size for the MutableSet type.")

        slots = tuple(f"_item{i}" for i in range(internal_size))
        namespace["__slots__"] = slots

        mcs._add_methods(slots, namespace, internal_size, project)

        return super().__new__(mcs, name, bases, namespace)

    @staticmethod
    def _add_methods(
        item_slots: Sequence[str],
        namespace: dict[str, Any],
        internal_size: int,
        project: Callable[[set], Set],
    ) -> None:
        def _assign_set(self, s):
            if len(s) > internal_size:
                setattr(self, item_slots[0], Overflow(s))
                for slot in item_slots[1:]:
                    setattr(self, slot, END)
            else:
                sentinel = object()
                for slot, v in zip_longest(item_slots, s, fillvalue=sentinel):
                    if v is sentinel:
                        setattr(self, slot, END)
                    else:
                        setattr(self, slot, v)

        def __init__(self, it):
            collected = it if isinstance(it, set) else set(it)
            _assign_set(self, collected)

        def __contains__(self, value):
            first = getattr(self, item_slots[0])
            if isinstance(first, Overflow):
                return value in first.data

            for slot in item_slots:
                v = getattr(self, slot)
                if v is END:
                    break
                if v == value:
                    return True
            return False

        def __iter__(self):
            first = getattr(self, item_slots[0])
            if isinstance(first, Overflow):
                yield from first.data
                return

            for slot in item_slots:
                v = getattr(self, slot)
                if v is END:
                    break
                yield v

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

        def add(self, value):
            current = set(self)
            current.add(value)
            _assign_set(self, current)

        def discard(self, value):
            current = set(self)
            current.discard(value)
            _assign_set(self, current)

        def __repr__(self):
            if len(self) == 0:
                return "set()"
            return f"{{{", ".join(repr(val) for val in self)}}}"

        def _from_iterable(_, it):
            return project(set(it))

        namespace["__init__"] = __init__
        namespace["__contains__"] = __contains__
        namespace["__iter__"] = __iter__
        namespace["__len__"] = __len__
        namespace["add"] = add
        namespace["discard"] = discard
        namespace["__repr__"] = __repr__
        namespace["_from_iterable"] = classmethod(_from_iterable)
