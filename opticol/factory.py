from collections.abc import (
    Callable,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Set,
)

from opticol._mapping import OptimizedMappingMeta, OptimizedMutableMappingMeta
from opticol._sequence import OptimizedMutableSequenceMeta, OptimizedSequenceMeta
from opticol._set import OptimizedMutableSetMeta, OptimizedSetMeta

# TODO: This needs a class registry to avoid unnecessary duplication of class creations.


def create_seq_class(size: int, project: Callable[[Sequence], Sequence]) -> type:
    return OptimizedSequenceMeta(
        f"_Size{size}Sequence",
        (Sequence,),
        {},
        internal_size=size,
        project=project,
    )


def create_mut_seq_class(size: int, project: Callable[[MutableSequence], MutableSequence]) -> type:
    return OptimizedMutableSequenceMeta(
        f"_Size{size}MutableSequence",
        (MutableSequence,),
        {},
        internal_size=size,
        project=project,
    )


def create_set_class(size: int, project: Callable[[Set], Set]) -> type:
    return OptimizedSetMeta(f"_Size{size}Set", (Set,), {}, internal_size=size, project=project)


def create_mut_set_class(size: int, project: Callable[[MutableSet], MutableSet]) -> type:
    return OptimizedMutableSetMeta(
        f"_Size{size}MutableSet",
        (MutableSet,),
        {},
        internal_size=size,
        project=project,
    )


def create_mapping_class(size: int) -> type:
    return OptimizedMappingMeta(f"_Size{size}Mapping", (Mapping,), {}, internal_size=size)


def create_mut_mapping_class(size: int) -> type:
    return OptimizedMutableMappingMeta(
        f"_Size{size}MutableMapping",
        (MutableMapping,),
        {},
        internal_size=size,
    )
