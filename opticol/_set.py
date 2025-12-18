from abc import ABCMeta
from itertools import zip_longest
from typing import Any, Callable

from collections.abc import Set

from opticol._sentinel import END, Overflow


class OptimizedSetMeta(ABCMeta):
    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        *,
        internal_size: int,
        project: Callable[[set], Set],
    ) -> type:
        slots = tuple(f"_item{i}" for i in range(internal_size)) if internal_size > 0 else ()
        namespace["__slots__"] = slots

        mcls._add_methods(slots, namespace, internal_size, project)

        return super().__new__(mcls, name, bases, namespace)

    @staticmethod
    def _add_methods(
        item_slots: tuple[str, ...],
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

        def __len__(self):
            return internal_size

        def __repr__(self):
            if internal_size == 0:
                return "set()"
            return f"{{{", ".join(repr(getattr(self, slot)) for slot in item_slots)}}}"

        def _from_iterable(cls, iter):
            return project(set(iter))

        namespace["__contains__"] = __contains__
        namespace["__iter__"] = __iter__
        namespace["__len__"] = __len__
        namespace["__repr__"] = __repr__
        namespace["_from_iterable"] = _from_iterable


class OptimizedMutableSetMeta(ABCMeta):
    def __new__(
        mcls,
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

        mcls._add_methods(slots, namespace, internal_size, project)

        return super().__new__(mcls, name, bases, namespace)

    @staticmethod
    def _add_methods(
        item_slots: tuple[str, ...],
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

        def __init__(self, iter):
            collected = set(iter) if type(iter) != set else iter
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

            for i, slot in enumerate(item_slots):
                if getattr(self, slot) is END:
                    return i

            return len(item_slots)

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

        def _from_iterable(cls, iter):
            return project(set(iter))

        namespace["__init__"] = __init__
        namespace["__contains__"] = __contains__
        namespace["__iter__"] = __iter__
        namespace["__len__"] = __len__
        namespace["add"] = add
        namespace["discard"] = discard
        namespace["__repr__"] = __repr__
        namespace["_from_iterable"] = _from_iterable
