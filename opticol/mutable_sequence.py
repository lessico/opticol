from collections.abc import MutableSequence
from opticol._sequence import OptimizedSequence


def _create_mut_seq_class(size: int, fallback: bool) -> type:
    def passthrough[T](c: list[T]) -> list[T]:
        return c

    fallback_slug = "Fallback" if fallback else ""
    fallback_project = passthrough if fallback else project
    return OptimizedSequence(
        f"Size{size}{fallback_slug}MutableSequence",
        (MutableSequence,),
        {},
        internal_size=size,
        mutable=True,
        project=fallback_project,
    )


_by_size: list[type] = []
_fallback_by_size: list[type] = []


def project[T](original: MutableSequence[T], fallback: bool = False) -> MutableSequence[T]:
    registry = _fallback_by_size if fallback else _by_size

    if len(original) >= len(registry):
        return original

    ctor = registry[len(original)]
    return ctor(*original)


def x() -> int:
    return 1


Size0MutableSequence = _create_mut_seq_class(0, False)
Size1MutableSequence = _create_mut_seq_class(1, False)
Size2MutableSequence = _create_mut_seq_class(2, False)
Size3MutableSequence = _create_mut_seq_class(3, False)

Size0FallbackMutableSequence = _create_mut_seq_class(0, True)
Size1FallbackMutableSequence = _create_mut_seq_class(1, True)
Size2FallbackMutableSequence = _create_mut_seq_class(2, True)
Size3FallbackMutableSequence = _create_mut_seq_class(3, True)

_by_size.extend(
    [Size0MutableSequence, Size1MutableSequence, Size2MutableSequence, Size3MutableSequence]
)
_fallback_by_size.extend(
    [
        Size0FallbackMutableSequence,
        Size1FallbackMutableSequence,
        Size2FallbackMutableSequence,
        Size3FallbackMutableSequence,
    ]
)
