from collections.abc import MutableSequence
from opticol._sequence import OptimizedMutableSequenceMeta


def _create_mut_seq_class(size: int) -> type:
    return OptimizedMutableSequenceMeta(
        f"Size{size}MutableSequence",
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


Size1MutableSequence = _create_mut_seq_class(1)
Size2MutableSequence = _create_mut_seq_class(2)
Size3MutableSequence = _create_mut_seq_class(3)

_by_size.extend(
    [Size1MutableSequence, Size1MutableSequence, Size2MutableSequence, Size3MutableSequence]
)
