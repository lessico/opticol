from collections.abc import Mapping
from opticol._mapping import OptimizedMappingMeta


def _create_mapping_class(size: int) -> type:
    return OptimizedMappingMeta(f"_Size{size}Mapping", (Mapping,), {}, internal_size=size)


_by_size: list[type] = []


def project[K, V](original: Mapping[K, V]) -> Mapping[K, V]:
    if len(original) >= len(_by_size):
        return original

    ctor = _by_size[len(original)]
    items = tuple(original.items())
    return ctor(*items)


_Size0Mapping = _create_mapping_class(0)
_Size1Mapping = _create_mapping_class(1)
_Size2Mapping = _create_mapping_class(2)
_Size3Mapping = _create_mapping_class(3)

_by_size.extend([_Size0Mapping, _Size1Mapping, _Size2Mapping, _Size3Mapping])
