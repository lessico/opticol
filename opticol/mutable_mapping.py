from collections.abc import MutableMapping
from opticol._mapping import OptimizedMutableMappingMeta


def _create_mut_mapping_class(size: int) -> type:
    return OptimizedMutableMappingMeta(
        f"_Size{size}MutableMapping",
        (MutableMapping,),
        {},
        internal_size=size,
    )


_by_size: list[type] = []


def project[K, V](original: MutableMapping[K, V]) -> MutableMapping[K, V]:
    if len(original) >= len(_by_size):
        return original

    ctor = _by_size[len(original)]
    return ctor(original)


_Size1MutableMapping = _create_mut_mapping_class(1)
_Size2MutableMapping = _create_mut_mapping_class(2)
_Size3MutableMapping = _create_mut_mapping_class(3)

_by_size.extend(
    [_Size1MutableMapping, _Size1MutableMapping, _Size2MutableMapping, _Size3MutableMapping]
)
