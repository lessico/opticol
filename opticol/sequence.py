from collections.abc import Sequence
from opticol._sequence import OptimizedSequenceMeta


def _create_seq_class(size: int) -> type:
    return OptimizedSequenceMeta(
        f"_Size{size}Sequence", (Sequence,), {}, internal_size=size, project=project
    )


_by_size: list[type] = []


def project[T](original: Sequence[T]) -> Sequence[T]:
    if len(original) >= len(_by_size):
        return original

    ctor = _by_size[len(original)]
    return ctor(*original)


_Size0Sequence = _create_seq_class(0)
_Size1Sequence = _create_seq_class(1)
_Size2Sequence = _create_seq_class(2)
_Size3Sequence = _create_seq_class(3)

_by_size.extend([_Size0Sequence, _Size1Sequence, _Size2Sequence, _Size3Sequence])
