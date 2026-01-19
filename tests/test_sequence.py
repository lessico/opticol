"""Test the memory optimized Sequence implementation for equivalence with builtins."""

from collections.abc import Callable, Sequence
from typing import Any

from opticol.factory import create_seq_class
from tests import seq, shared
from tests.seq import getitem, contains, index, count


def harness[T](
    seed: Sequence[T],
    ops: Sequence[Callable[[Sequence], Any]],
) -> None:
    """
    The wrapper around the main test harness implementation.

    Checks that for a given seed or start Sequence value, the set of provided operations have the
    same result on the optimized and the builtin Sequence implementations.

    Args:
        seed: The Sequence value to create the various implementations with for testing.
        ops: The operations whose behavior needs to be validated across builtins and optimized
            variants.
    """
    factories = [list, tuple, create_seq_class(len(seed))]
    shared.harness(seed, factories, ops, seq.eq, seq.eq_op_result)


def test_seq_getitem_indices():
    """Test that optimized sequences handle getitem with single indices correctly."""
    # Indexing with a single value within the sequence bounds.
    harness(
        [4, 5, 6],
        [getitem(-1), getitem(0), getitem(1), getitem(2), getitem(3), getitem(-2), getitem(-3)],
    )


def test_seq_getitem_basic_slices():
    """Test that optimized sequences handle getitem with basic slices correctly."""
    # Indexing with slices within the sequence bounds.
    harness(
        [4, 5, 6],
        [getitem(slice(0, -1)), getitem(slice(-1, -1)), getitem(slice(None)), getitem(slice(1, 3))],
    )


def test_seq_getitem_step_slices():
    """Test that optimized sequences handle slices with step values correctly."""
    # Reverse slicing
    harness(
        [1, 2, 3, 4, 5],
        [getitem(slice(None, None, -1)), getitem(slice(4, 0, -1)), getitem(slice(4, None, -1))],
    )

    # Step size > 1
    harness(
        [0, 1, 2, 3, 4],
        [getitem(slice(None, None, 2)), getitem(slice(1, None, 2)), getitem(slice(0, 5, 2))],
    )

    # Negative step with explicit bounds
    harness(
        [10, 20, 30, 40],
        [getitem(slice(3, 0, -1)), getitem(slice(3, None, -2)), getitem(slice(-1, -4, -1))],
    )

    # Step on empty sequence
    harness(
        [],
        [getitem(slice(None, None, 2)), getitem(slice(None, None, -1))],
    )

    # Step on single element
    harness(
        [42],
        [getitem(slice(None, None, 2)), getitem(slice(None, None, -1)), getitem(slice(0, 1, 3))],
    )


def test_seq_getitem_out_of_bounds_slices():
    """Test that optimized sequences handle out-of-bounds slices correctly."""
    # Empty sequence should always return on getitem with a slice.
    harness(
        [],
        [getitem(slice(0, -1)), getitem(slice(-1, -1)), getitem(slice(None))],
    )

    # Slices that extend beyond sequence bounds should be clamped
    harness(
        [1, 2, 3],
        [
            getitem(slice(0, 100)),
            getitem(slice(-100, 100)),
            getitem(slice(5, 10)),
            getitem(slice(-10, -5)),
        ],
    )

    # Large step values
    harness(
        [1, 2, 3, 4, 5],
        [getitem(slice(0, 5, 100)), getitem(slice(4, 0, -100))],
    )

    # Mixed large bounds
    harness(
        [10, 20],
        [getitem(slice(-1000, 1000)), getitem(slice(1000, -1000, -1))],
    )


def test_seq_len():
    """Test that optimized sequences have the same len semantics as builtins."""
    harness(
        [],
        [len],
    )

    harness(
        [3.14],
        [len],
    )

    harness(
        [3.14, 2.71],
        [len],
    )

    harness(
        [None, None, None],
        [len],
    )


def test_seq_contains():
    """Test that optimized sequences have the same contains semantics as builtins."""

    harness(
        [1, 2, 3],
        [contains(1), contains(2), contains(3), contains(4, False)],
    )

    harness(
        [],
        [contains(0, False), contains(1, False), contains(None, False)],
    )

    harness(
        [None],
        [contains(None)],
    )

    harness(
        [100],
        [contains(0, False), contains(100)],
    )

    # int/float equality
    harness(
        [1.0, 2.0, 3.0],
        [contains(1.0), contains(2), contains(3)],
    )


def test_seq_iter():
    """Test that optimized sequences have the same iter semantics as builtins."""
    harness(
        [],
        [iter],
    )

    harness(
        [True],
        [iter],
    )

    harness(
        [False, True],
        [iter],
    )

    harness(
        [3.14, 2.71, -1],
        [iter],
    )


def test_seq_reversed():
    """Test that optimized sequences have the same reversed semantics as builtins."""
    harness(
        [],
        [reversed],
    )

    harness(
        [True],
        [reversed],
    )

    harness(
        [False, True],
        [reversed],
    )

    harness(
        [3.14, 2.71, -1],
        [reversed],
    )


def test_seq_index():
    """Test that optimized sequences have the same index semantics as builtins."""
    harness(
        [],
        [index(0), index(-1), index(4)],
    )

    harness(
        [10, 11],
        [index(10), index(9), index(11, 1), index(11, 0, 0)],
    )


def test_seq_index_negative_bounds():
    """Test that optimized sequences handle negative start/stop for index."""
    harness(
        [10, 20, 30, 40, 50],
        [index(30, -3), index(50, -2), index(10, -5, -1), index(20, -4, 2)],
    )

    harness(
        [1, 2, 3],
        [index(1, -2), index(3, 0, -1)],
    )


def test_seq_index_duplicates():
    """Test that index returns the first occurrence with duplicates."""
    harness(
        [5, 5, 5],
        [index(5), index(5, 1), index(5, 2)],
    )

    harness(
        [1, 2, 1, 2, 1],
        [index(1), index(1, 1), index(1, 3), index(2), index(2, 2)],
    )

    harness(
        [None, 0, None, 0],
        [index(None), index(None, 1), index(0), index(0, 2)],
    )


def test_seq_count():
    """Test that optimized sequences have the same count semantics as builtins."""

    harness(
        [],
        [count(1), count(None)],
    )

    harness(
        [None],
        [count(1), count(None)],
    )

    harness(
        [1, 1, None],
        [count(1), count(None)],
    )

    harness(
        [7, 7, 7, 7, 7],
        [count(7), count(0)],
    )

    # Count with equality edge cases (True == 1, False == 0)
    harness(
        [True, 1, 1, False, 0],
        [count(True), count(1), count(False), count(0)],
    )

    harness(
        [None, None],
        [count(None)],
    )


def test_seq_larger_sequences():
    """Test that optimized sequences work correctly with 4 and 5 element counts."""
    harness(
        [1, 2, 3, 4],
        [
            len,
            getitem(0),
            getitem(3),
            getitem(-1),
            getitem(slice(1, 3)),
            getitem(slice(None, None, 2)),
            contains(2),
            contains(5, False),
            index(3),
            count(1),
            iter,
            reversed,
        ],
    )

    harness(
        [10, 20, 30, 40, 50],
        [
            len,
            getitem(slice(1, 4, 2)),
            getitem(slice(None, None, -1)),
            index(40),
            index(30, 1, 4),
        ],
    )


def test_seq_mixed_types():
    """Test that optimized sequences handle mixed element types correctly."""
    harness(
        [1, "two", 3.0, None, True],
        [
            len,
            getitem(0),
            getitem(1),
            getitem(2),
            contains(1),
            contains("two"),
            contains(3.0),
            contains(None),
            contains(True),
            index(1),
            index("two"),
            index(None),
            count(1),
            count(None),
            iter,
            reversed,
        ],
    )

    # Note: True == 1 and False == 0 in Python
    harness(
        [True, False, 1, 0],
        [contains(True), contains(1), contains(False), contains(0), count(True), count(1)],
    )
