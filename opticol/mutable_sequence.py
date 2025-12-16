from collections.abc import MutableSequence
from opticol._sequence import OptimizedMutableSequenceMeta


def _create_mut_seq_class(size: int) -> type:
    return OptimizedMutableSequenceMeta(
        f"_Size{size}MutableSequence",
        (MutableSequence,),
        {},
        internal_size=size,
        project=project,
    )


_by_size: list[type] = []


def project[T](original: MutableSequence[T]) -> MutableSequence[T]:
    if len(original) >= len(_by_size):
        return original

    ctor = _by_size[len(original)]
    return ctor(original)


_Size1MutableSequence = _create_mut_seq_class(1)
_Size2MutableSequence = _create_mut_seq_class(2)
_Size3MutableSequence = _create_mut_seq_class(3)

_by_size.extend(
    [_Size1MutableSequence, _Size1MutableSequence, _Size2MutableSequence, _Size3MutableSequence]
)
