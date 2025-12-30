from abc import ABCMeta
from typing import Any


class OptimizedCollectionMeta(ABCMeta):
    _index = 0

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> type:
        mcs._index += 1
        formatted_name = f"{name}_{mcs._index}"
        return super().__new__(mcs, formatted_name, bases, namespace)
