from collections.abc import (
    Callable,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Set,
)
import functools
from typing import Optional

from opticol._mapping import OptimizedMappingMeta, OptimizedMutableMappingMeta
from opticol._sequence import OptimizedMutableSequenceMeta, OptimizedSequenceMeta
from opticol._set import OptimizedMutableSetMeta, OptimizedSetMeta

def cached(func):
    cache = {}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            key = (args, tuple(sorted(kwargs.items())))
            hash(key)
        except TypeError:
            return func(*args, **kwargs)

        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]

    return wrapper


@cached
def create_seq_class(size: int, project: Optional[Callable[[Sequence], Sequence]] = None) -> type:
    return OptimizedSequenceMeta(
        f"_Size{size}Sequence",
        (Sequence,),
        {},
        internal_size=size,
        project=project,
    )


@cached
def create_mut_seq_class(size: int, project: Optional[Callable[[MutableSequence], MutableSequence]]) -> type:
    return OptimizedMutableSequenceMeta(
        f"_Size{size}MutableSequence",
        (MutableSequence,),
        {},
        internal_size=size,
        project=project,
    )


@cached
def create_set_class(size: int, project: Optional[Callable[[Set], Set]] = None) -> type:
    return OptimizedSetMeta(f"_Size{size}Set", (Set,), {}, internal_size=size, project=project)


@cached
def create_mut_set_class(size: int, project: Optional[Callable[[MutableSet], MutableSet]] = None) -> type:
    return OptimizedMutableSetMeta(
        f"_Size{size}MutableSet",
        (MutableSet,),
        {},
        internal_size=size,
        project=project,
    )


@cached
def create_mapping_class(size: int) -> type:
    return OptimizedMappingMeta(f"_Size{size}Mapping", (Mapping,), {}, internal_size=size)


@cached
def create_mut_mapping_class(size: int) -> type:
    return OptimizedMutableMappingMeta(
        f"_Size{size}MutableMapping",
        (MutableMapping,),
        {},
        internal_size=size,
    )
