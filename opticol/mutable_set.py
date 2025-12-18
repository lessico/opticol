from collections.abc import MutableSet
from opticol._set import OptimizedMutableSetMeta


def _create_mut_set_class(size: int) -> type:
    return OptimizedMutableSetMeta(
        f"_Size{size}MutableSet",
        (MutableSet,),
        {},
        internal_size=size,
        project=project,
    )


_by_size: list[type] = []


def project[T](original: MutableSet[T]) -> MutableSet[T]:
    if len(original) >= len(_by_size):
        return original

    ctor = _by_size[len(original)]
    return ctor(original)


_Size1MutableSet = _create_mut_set_class(1)
_Size2MutableSet = _create_mut_set_class(2)
_Size3MutableSet = _create_mut_set_class(3)

_by_size.extend([_Size1MutableSet, _Size1MutableSet, _Size2MutableSet, _Size3MutableSet])
