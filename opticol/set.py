from collections.abc import Set
from opticol._set import OptimizedSetMeta


def _create_set_class(size: int) -> type:
    return OptimizedSetMeta(f"_Size{size}Set", (Set,), {}, internal_size=size, project=project)


_by_size: list[type] = []


def project[T](original: Set[T]) -> Set[T]:
    if len(original) >= len(_by_size):
        return original

    ctor = _by_size[len(original)]
    return ctor(*original)


_Size0Set = _create_set_class(0)
_Size1Set = _create_set_class(1)
_Size2Set = _create_set_class(2)
_Size3Set = _create_set_class(3)

_by_size.extend([_Size0Set, _Size1Set, _Size2Set, _Size3Set])
