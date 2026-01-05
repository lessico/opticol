from collections.abc import Callable, Iterator, Sequence
import sys
from typing import Any

from opticol.factory import create_mut_seq_class, create_seq_class


type Factory[T] = Callable[[Sequence[T]], Sequence[T]]


def eq_seq[T](seq1: Sequence[T], seq2: Sequence[T]) -> bool:
    if len(seq1) != len(seq2):
        return False

    for item1, item2 in zip(seq1, seq2):
        if item1 != item2:
            return False

    return True

def eq_op_result[T, U](first: T, second: U) -> bool:
    # The result of the operations on a Sequence's API surface area are either an Iterator, a
    # Sequence, or an item from the Sequence.
    if isinstance(first, Iterator) and isinstance(second, Iterator):
        return eq_seq(list(first), list(second))
    elif isinstance(first, Sequence) and isinstance(second, Sequence):
        return eq_seq(first, second)
    elif type(first) == type(second):
        return first == second

    return False


def harness[T](
    target_factory: Factory[T],
    reference_factory: Factory[T],
    seed: Sequence[T],
    ops: Sequence[Callable[[Sequence], Any]],
) -> None:
    target = target_factory(seed)
    reference = reference_factory(seed)

    for op in ops:
        target_result = op(target)
        reference_result = op(reference)

        assert eq_op_result(target_result, reference_result)
        assert eq_seq(target, reference)


def getitem[T](key: int | slice) -> Callable[[Sequence[T]], T | Sequence[T]]:
    return lambda s: s[key]

def contains[T, U](other: object) -> Callable[[Sequence[T]], bool]:
    return lambda s: other in s

def index[T](val: Any, start: int = 0, stop: int = sys.maxsize, /) -> Callable[[Sequence[T]], int]:
    return lambda s: s.index(val, start, stop)

def count[T](val: Any) -> Callable[[Sequence[T]], int]:
    return lambda s: s.count(val)


def test_first():
    harness(create_seq_class(3), list, [1, 2, 3], [
        contains(1),
        count(2)
    ])
