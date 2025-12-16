from collections.abc import Sequence
from opticol._sequence import OptimizedSequenceMeta


def _create_seq_class(size: int) -> type:
    return OptimizedSequenceMeta(
        f"Size{size}Sequence", (Sequence,), {}, internal_size=size, project=project
    )


_by_size: list[type] = []


def project[T](original: Sequence[T]) -> Sequence[T]:
    if len(original) >= len(_by_size):
        return original

    ctor = _by_size[len(original)]
    return ctor(*original)


Size0Sequence = _create_seq_class(0)
Size1Sequence = _create_seq_class(1)
Size2Sequence = _create_seq_class(2)
Size3Sequence = _create_seq_class(3)

_by_size.extend([Size0Sequence, Size1Sequence, Size2Sequence, Size3Sequence])
