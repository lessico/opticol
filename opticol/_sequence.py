from itertools import zip_longest
from typing import Any

from collections.abc import Callable, Sequence

from opticol._meta import OptimizedCollectionMeta
from opticol._sentinel import END, Overflow

# TODO: For RO collection types, change so that ziplongest is not used, since
# we are not projecting from an iterator.
# TODO: Add slash at the end of the methods so that keywords are not allowed
# TODO: Change DefaultProjector to SmallCollectionProjector and then allow for parameters of up to
# what size optimizations are used up to (allows it to easily be composed by others in other strategies
# or create in other ways).
# TODO: Add documentation that projector is supposed to be a vocabulary type that should be used where
# collection strategy should be pluggable.
# TODO: Add default value for project so that users can more reliably use the class creation methods.

# TODO: Consider if there is anyway to compose the projectors easily in authoring as well such as composable
# allocators ideas and such.

# TODO: Projection from iterators into the sequence types can also be optimized and is an area that can
# be supported in the future via a *_from_iter method which in the default case materializes the view
# in memory (or does throw a runtime exception so that it's not used inappropriately). The idea is that
# this would optimize an iterable becoming a certain collection type.


def _adjust_index(idx: int, length: int) -> int:
    adjusted = idx if idx >= 0 else length + idx
    if adjusted < 0 or adjusted >= length:
        raise IndexError(f"{adjusted} is outside of the expected bounds.")
    return adjusted


class OptimizedSequenceMeta(OptimizedCollectionMeta):
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
        def __init__(self, seq):
            if len(seq) != internal_size:
                raise ValueError(
                    f"Expected provided iterator to have exactly {internal_size} elements but has {len(seq)}."
                )

            sentinel = object()
            for slot, v in zip_longest(item_slots, seq, fillvalue=sentinel):
                setattr(self, slot, v)

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

        namespace["__init__"] = __init__
        namespace["__getitem__"] = __getitem__
        namespace["__len__"] = __len__
        namespace["__repr__"] = __repr__


class OptimizedMutableSequenceMeta(OptimizedCollectionMeta):
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
        def _assign(self, seq):
            if len(seq) > internal_size:
                setattr(self, item_slots[0], Overflow(seq))
                for slot in item_slots[1:]:
                    setattr(self, slot, END)
            else:
                sentinel = object()
                for slot, v in zip_longest(item_slots, seq, fillvalue=sentinel):
                    if v is sentinel:
                        setattr(self, slot, END)
                    else:
                        setattr(self, slot, v)

        def __init__(self, seq):
            _assign(self, seq)

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
            _assign(self, current)

        def __delitem__(self, key):
            current = list(self)
            del current[key]
            _assign(self, current)

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
            _assign(self, current)

        def __repr__(self):
            return f"[{", ".join(repr(val) for val in self)}]"

        namespace["__init__"] = __init__
        namespace["__getitem__"] = __getitem__
        namespace["__setitem__"] = __setitem__
        namespace["__delitem__"] = __delitem__
        namespace["__len__"] = __len__
        namespace["insert"] = insert
        namespace["__repr__"] = __repr__
