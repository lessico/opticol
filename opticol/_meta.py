from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Iterable, Iterator, Sequence
from typing import Any, Optional


class OptimizedCollectionMeta[C](ABCMeta):
    _index = 0

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        *,
        internal_size: int,
        project: Optional[Callable[[C], C]],
        collection_name: str,
    ) -> type:
        OptimizedCollectionMeta._index += 1
        formatted_name = f"{name}_{OptimizedCollectionMeta._index}"

        if internal_size < 0:
            raise ValueError(f"{internal_size} is not a valid size for the {collection_name} type.")

        slots = tuple(f"_item{i}" for i in range(internal_size))
        namespace["__slots__"] = slots

        mcs.add_methods(slots, namespace, internal_size, project)

        return super().__new__(mcs, formatted_name, bases, namespace)

    @staticmethod
    @abstractmethod
    def add_methods(
        slots: Sequence[str],
        namespace: dict[str, Any],
        internal_size: int,
        project: Optional[Callable[[C], C]],
    ): ...

    @staticmethod
    def _mut_len[O](
        inst: Any,
        slots: Sequence[str],
        overflow_type: type[O],
        overflow_selector: Callable[[O], int],
        end_object: object,
    ) -> int:
        first = getattr(inst, slots[0])
        if isinstance(first, overflow_type):
            return overflow_selector(first)

        count = 0
        for slot in slots:
            if getattr(inst, slot) is end_object:
                break
            count += 1

        return count

    @staticmethod
    def _mut_iter[O](
        inst: Any,
        slots: Sequence[str],
        overflow_type: type[O],
        overflow_selector: Callable[[O], Iterable],
        end_object: object,
        value_selector: Callable,
    ) -> Iterator:
        first = getattr(inst, slots[0])
        if isinstance(first, overflow_type):
            yield from overflow_selector(first)
            return

        for slot in slots:
            v = getattr(inst, slot)
            if v is end_object:
                return
            yield value_selector(v)
