from abc import ABCMeta
from typing import Any, Callable

from collections.abc import Sequence


class OptimizedSequence(ABCMeta):
    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        *,
        internal_size: int,
        mutable: bool,
        project: Callable[[list], Sequence],
    ) -> type:
        slots = tuple(f"_item{i}" for i in range(internal_size)) if internal_size > 0 else ()
        namespace["__slots__"] = slots

        if "__class_getitem__" not in namespace:
            namespace["__class_getitem__"] = classmethod(lambda cls, _: cls)

        mcls._add_general_methods(slots, namespace)
        mcls._add_read_methods(slots, namespace, internal_size, project)
        if mutable:
            mcls._add_write_methods(namespace, project)

        return super().__new__(mcls, name, bases, namespace)

    @staticmethod
    def _add_general_methods(item_slots: Sequence[str], namespace: dict[str, Any]) -> None:
        def __str__(self):
            return f"[{", ".join(repr(getattr(self, slot)) for slot in item_slots)}]"

        namespace["__str__"] = __str__

    @staticmethod
    def _add_read_methods(
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
                    key = key if key >= 0 else len(self) + key
                    if key < 0 or key >= internal_size:
                        raise IndexError(f"{key} is not a valid index for this Collection.")
                    return getattr(self, item_slots[key])
                case slice():
                    indices = range(*key.indices(len(self)))
                    return project([self[i] for i in indices])
                case _:
                    raise TypeError(
                        f"Sequence accessors must be integers or slices., not {type(key)}"
                    )

        def __len__(self):
            return internal_size

        namespace["__getitem__"] = __getitem__
        namespace["__len__"] = __len__

    @staticmethod
    def _add_write_methods(namespace: dict[str, Any], project: Callable[[list], Sequence]) -> None:
        def __setitem__(self, key, value):
            current = list(iter(self))
            current[key] = value
            return project(current)

        def __delitem__(self, key):
            current = list(iter(self))
            del current[key]
            return project(current)

        def insert(self, index, value):
            current = list(iter(self))
            current.insert(index, value)
            return project(current)

        namespace["__setitem__"] = __setitem__
        namespace["__delitem__"] = __delitem__
        namespace["insert"] = insert
