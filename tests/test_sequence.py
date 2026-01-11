from collections.abc import Callable, Iterator, Sequence
import sys
from typing import Any

from opticol.factory import create_seq_class

type Factory[T] = Callable[[Sequence[T]], Sequence[T]]


def _success_label(success: bool) -> str:
    if success:
        return "succeeded"

    return "failed"


def eq_seq[T](seq1: Sequence[T], seq2: Sequence[T]) -> bool:
    """
    Return if two sequences are identical at the Sequence interface level.

    Args:
        seq1: One of the sequences to compare for equality.
        seq2: The other sequence to compare for equality.

    Returns:
        True if the two sequences are identical and False otherwise.
    """
    if len(seq1) != len(seq2):
        return False

    for item1, item2 in zip(seq1, seq2):
        if item1 != item2:
            return False

    return True



def eq_op_result[T, U](first: T, second: U, materialized_cache: dict[Iterator, list]) -> bool:
    """
    Checks if the result of two Sequence operations are identical.

    The results are obtained if the Sequence operation succeeds and does not raise an error.
    Sequence operation here refers to those operations defined on the ABC collection documentation
    as required to implement, and mixins.

    Based on this documentation, the only possible results from a Sequence operation are an
    Iterator, another Sequence, an item from the Sequence or a boolean.

    Args:
        first: The first result to compare.
        second: The second result to compare.
        materialized_cache: The per harness cache of iterators their in-memory materialized version.

    Returns:
        True if the results of the operation are identical, and False otherwise.
    """
    if isinstance(first, Iterator) and isinstance(second, Iterator):
        if first not in materialized_cache:
            materialized_cache[first] = list(first)
        f = materialized_cache[first]

        if second not in materialized_cache:
            materialized_cache[second] = list(second)
        s = materialized_cache[second]

        return eq_seq(f, s)
    elif isinstance(first, Sequence) and isinstance(second, Sequence):
        return eq_seq(first, second)

    # The results of the operations are either elements from the sequence or a boolean.
    return first == second


def assert_eq_op[T, U](unk: tuple[bool, T], ref: tuple[bool, U], unk_idx: int, op_idx: int, materialized_cache: dict[Iterator, list]) -> None:
    """
    Assert that two operations on a Sequence have the same output.

    The operation if successful, has some output, but in the error case, will raise an error. So the
    first value is a flag if the operation was successful, and the second value is either the result
    of the operation or the error that was raised.

    Args:
        unk: The result that is being compared against a reference.
        ref: The reference being compared against.
        unk_idx: Used for crafing the assert message in the case of any failure. Indexes the unknown
            sequence instance.
        op_idx: The operation index operating on the different sequence instances.
        materialized_list: The per harness cache of iterators to lists.
    """
    assert unk[0] == ref[0], (
        f"The operation at index {op_idx} {_success_label(unk[0])} on the factory at index "
        f"{unk_idx} with result '{ref[1]}' while the first factory {_success_label(ref[0])} "
        f"with result {ref[1]}."
    )

    # If the operation did not raise any error, then just compare the results otherwise, the
    # error check just ensures that they are the same error types, since there is no other
    # reliable and deeper comparison available.
    if unk[0]:
        assert eq_op_result(unk[1], ref[1], materialized_cache)
    else:
        assert type(unk[1]) == type(ref[1])


def harness[T](
    seed: Sequence[T],
    factories: Sequence[Factory[T]],
    ops: Sequence[Callable[[Sequence], Any]],
) -> None:
    """
    The main test harness for Sequences and which can be used to establish API level equivalence.

    There are technically no behavior level definitions of Sequences and there are a lot of edge
    cases, so the easiest way to test behavior is to compare the effects and results of different
    implementations on various interface definitions.

    Args:
        seed: The value that is provided to the various factories to create the Sequence instances.
        factories: The implementations to test via the harness.
        ops: The operations to call on the Sequence. The results will be validated and any mutations
            to the underlying Sequence will be compared as well.
    """
    if len(factories) < 2:
        raise ValueError("Expected at least two factories to compare operations on.")

    materialized_cache: dict[Iterator, list] = {}

    targets = [factory(seed) for factory in factories]

    def exec(current, op):
        successful = True
        try:
            result = op(current)
        except Exception as exc:
            successful = False
            result = exc

        return (successful, result)

    for i, op in enumerate(ops):
        results = [exec(target, op) for target in targets]

        for j, sub in enumerate(results[1:], 1):
            assert_eq_op(sub, results[0], j, i, materialized_cache)

        for target in targets[1:]:
            assert eq_seq(targets[0], target)


def getitem[T](key: int | slice) -> Callable[[Sequence[T]], T | Sequence[T]]:
    """Create a callable which wraps getitem and calls it on the given Sequence."""
    return lambda s: s[key]


def contains[T](other: object, result: bool = True) -> Callable[[Sequence[T]], bool]:
    """Create a callable which wraps contains and calls it on the given Sequence."""
    return lambda s: (other in s == result)


def index[T](val: Any, start: int = 0, stop: int = sys.maxsize, /) -> Callable[[Sequence[T]], int]:
    """Create a callable which wraps index and calls it on the given Sequence."""
    return lambda s: s.index(val, start, stop)


def count[T](val: Any) -> Callable[[Sequence[T]], int]:
    """Create a callable which wraps count and calls it on the given Sequence."""
    return lambda s: s.count(val)


def test_seq_getitem():
    """Test that optimized sequences have the same getitem semantics as builtins."""
    harness(
        [4, 5, 6],
        [list, tuple, create_seq_class(3)],
        [getitem(-1), getitem(0), getitem(1), getitem(2), getitem(3), getitem(-2), getitem(-3)],
    )

    harness(
        [4, 5, 6],
        [list, tuple, create_seq_class(3)],
        [getitem(slice(0, -1)), getitem(slice(-1, -1)), getitem(slice(None)), getitem(slice(1, 3))],
    )

    harness(
        [],
        [list, tuple, create_seq_class(0)],
        [getitem(slice(0, -1)), getitem(slice(-1, -1)), getitem(slice(None))],
    )


def test_seq_contains():
    """Test that optimized sequences have the same contains semantics as builtins."""

    harness(
        [1, 2, 3],
        [list, tuple, create_seq_class(3)],
        [contains(1), contains(2), contains(3), contains(4, False)],
    )

    harness([], [list, create_seq_class(0)], [contains(0, False), contains(1, False)])

    harness([100], [list, tuple, create_seq_class(1)], [contains(0, False), contains(100)])


def test_seq_index():
    """Test that optimized sequences have the same index semantics as builtins."""

    harness(
        [],
        [list, tuple, create_seq_class(0)],
        [index(0), index(-1), index(4)]
    )

    harness(
        [10, 11],
        [list, tuple, create_seq_class(2)],
        [index(10), index(9), index(11, 1), index(11, 0, 0)]
    )


def test_seq_iter():
    """Test that optimized sequences have the same iter semantics as builtins."""
    harness(
        [],
        [list, tuple, create_seq_class(0)],
        [iter]
    )

    harness(
        [3.14, 2.71, -1],
        [list, tuple, create_seq_class(3)],
        [iter]
    )


def test_seq_count():
    """Test that optimized sequences have the same count semantics as builtins."""

    harness(
        [],
        [list, tuple, create_seq_class(0)],
        [count(1), count(None)]
    )

    harness(
        [None],
        [list, tuple, create_seq_class(1)],
        [count(1), count(None)]
    )

    harness(
        [1, 1, None],
        [list, tuple, create_seq_class(3)],
        [count(1), count(None)]
    )