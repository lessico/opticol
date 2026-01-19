"""Test the memory optimized MutableSequence implementation for equivalence with builtins."""

from collections.abc import Callable, MutableSequence
from typing import Any

from opticol.factory import create_mut_seq_class
from tests import seq, shared
from tests.seq import getitem, contains, index, count


def harness[T](
    seed: MutableSequence[T],
    ops: list[Callable[[MutableSequence], Any]],
    internal_sizes: list[int] | None = None,
) -> None:
    """
    The wrapper around the main test harness implementation.

    Checks that for a given seed or start MutableSequence value, the set of provided operations
    have the same result on the optimized variants and the builtin list implementation.

    Args:
        seed: The MutableSequence value to create the various implementations with for testing.
        ops: The operations whose behavior needs to be validated across builtins and optimized
            variants.
        internal_sizes: The internal slot sizes for the optimized collections. When None, uses
            [len(seed)] for exact size matching. When specified, creates an optimized collection
            for each size, allowing testing of overflow behavior (size < len(seed)) or growth
            into available slots (size > len(seed)).
    """
    sizes = internal_sizes if internal_sizes is not None else [len(seed)]
    factories: list[shared.Factory[MutableSequence[T]]] = [list] + [
        create_mut_seq_class(size) for size in sizes
    ]
    shared.harness(seed, factories, ops, seq.eq, seq.eq_op_result)


def setitem[T](key: int | slice, value: T) -> Callable[[MutableSequence[T]], None]:
    """Create a callable which wraps setitem and calls it on the given MutableSequence."""

    def op(s):
        s[key] = value

    return op


def delitem(key: int | slice) -> Callable[[MutableSequence], None]:
    """Create a callable which wraps delitem and calls it on the given MutableSequence."""

    def op(s):
        del s[key]

    return op


def insert[T](idx: int, value: T) -> Callable[[MutableSequence[T]], None]:
    """Create a callable which wraps insert and calls it on the given MutableSequence."""

    def op(s):
        s.insert(idx, value)

    return op


def append[T](value: T) -> Callable[[MutableSequence[T]], None]:
    """Create a callable which wraps append and calls it on the given MutableSequence."""

    def op(s):
        s.append(value)

    return op


def clear() -> Callable[[MutableSequence], None]:
    """Create a callable which wraps clear and calls it on the given MutableSequence."""

    def op(s):
        s.clear()

    return op


def reverse() -> Callable[[MutableSequence], None]:
    """Create a callable which wraps reverse and calls it on the given MutableSequence."""

    def op(s):
        s.reverse()

    return op


def extend[T](values: list[T]) -> Callable[[MutableSequence[T]], None]:
    """Create a callable which wraps extend and calls it on the given MutableSequence."""

    def op(s):
        s.extend(values)

    return op


def pop(idx: int | None = None) -> Callable[[MutableSequence], Any]:
    """Create a callable which wraps pop and calls it on the given MutableSequence."""
    if idx is None:
        idx = -1
    return lambda s: s.pop(idx)


def remove[T](value: T) -> Callable[[MutableSequence[T]], None]:
    """Create a callable which wraps remove and calls it on the given MutableSequence."""

    def op(s):
        s.remove(value)

    return op


def iadd[T](values: list[T]) -> Callable[[MutableSequence[T]], MutableSequence[T]]:
    """Create a callable which wraps __iadd__ and calls it on the given MutableSequence."""

    def op(s):
        s += values

    return op


def test_mut_seq_len():
    """Test that optimized mutable sequences have the same len semantics as list."""
    harness([], [len])
    harness([1], [len])
    harness([1, 2], [len])
    harness([1, 2, 3], [len])


def test_mut_seq_getitem_indices():
    """Test that optimized mutable sequences handle getitem with single indices correctly."""
    harness(
        [4, 5, 6],
        [getitem(-1), getitem(0), getitem(1), getitem(2), getitem(3), getitem(-2), getitem(-3)],
    )


def test_mut_seq_getitem_slices():
    """Test that optimized mutable sequences handle getitem with slices correctly."""
    harness(
        [1, 2, 3, 4, 5],
        [
            getitem(slice(None)),
            getitem(slice(1, 3)),
            getitem(slice(None, None, -1)),
            getitem(slice(0, 5, 2)),
            getitem(slice(-1000, 1000)),
        ],
    )


def test_mut_seq_setitem_indices():
    """Test that optimized mutable sequences handle setitem with single indices correctly."""
    harness([1, 2, 3], [setitem(0, 100), getitem(0)])
    harness([1, 2, 3], [setitem(-1, 100), getitem(-1)])
    harness([1, 2, 3], [setitem(1, 100), getitem(1)])

    # Out of bounds setitem
    harness([1, 2, 3], [setitem(5, 100)])
    harness([1, 2, 3], [setitem(-5, 100)])


def test_mut_seq_setitem_slices():
    """Test that optimized mutable sequences handle setitem with slices correctly."""
    harness([1, 2, 3, 4], [setitem(slice(1, 3), [10, 20]), len, getitem(slice(None))])
    harness([1, 2, 3], [setitem(slice(None), []), len])
    harness([1, 2, 3], [setitem(slice(0, 2), [10, 20, 30, 40]), len, getitem(slice(None))])


def test_mut_seq_delitem_indices():
    """Test that optimized mutable sequences handle delitem with single indices correctly."""
    harness([1, 2, 3], [delitem(0), len, getitem(slice(None))])
    harness([1, 2, 3], [delitem(-1), len, getitem(slice(None))])
    harness([1, 2, 3], [delitem(1), len, getitem(slice(None))])

    # Out of bounds delitem
    harness([1, 2, 3], [delitem(5)])
    harness([1, 2, 3], [delitem(-5)])


def test_mut_seq_delitem_slices():
    """Test that optimized mutable sequences handle delitem with slices correctly."""
    harness([1, 2, 3, 4, 5], [delitem(slice(1, 3)), len, getitem(slice(None))])
    harness([1, 2, 3], [delitem(slice(None)), len])
    harness([1, 2, 3, 4], [delitem(slice(None, None, 2)), len, getitem(slice(None))])


def test_mut_seq_insert():
    """Test that optimized mutable sequences handle insert correctly."""
    harness([1, 2, 3], [insert(0, 100), len, getitem(0)])
    harness([1, 2, 3], [insert(1, 100), len, getitem(1)])
    harness([1, 2, 3], [insert(-1, 100), len, getitem(slice(None))])
    harness([1, 2, 3], [insert(100, 100), len, getitem(-1)])

    # Insert into empty
    harness([], [insert(0, 100), len, getitem(0)])


def test_mut_seq_contains():
    """Test that optimized mutable sequences have the same contains semantics as list."""
    harness([1, 2, 3], [contains(1), contains(2), contains(3), contains(4, False)])
    harness([], [contains(0, False), contains(None, False)])
    harness([None], [contains(None)])


def test_mut_seq_iter():
    """Test that optimized mutable sequences have the same iter semantics as list."""
    harness([], [iter])
    harness([1], [iter])
    harness([1, 2, 3], [iter])


def test_mut_seq_reversed():
    """Test that optimized mutable sequences have the same reversed semantics as list."""
    harness([], [reversed])
    harness([1], [reversed])
    harness([1, 2, 3], [reversed])


def test_mut_seq_index():
    """Test that optimized mutable sequences have the same index semantics as list."""
    harness([], [index(0)])
    harness([10, 20, 30], [index(10), index(20), index(30), index(40)])
    harness([1, 2, 1, 2], [index(1), index(1, 1), index(2, 2)])


def test_mut_seq_count():
    """Test that optimized mutable sequences have the same count semantics as list."""
    harness([], [count(1)])
    harness([1, 1, 2, 1], [count(1), count(2), count(3)])
    harness([None, None], [count(None)])


# Tests for MutableSequence mixin methods: append, clear, reverse, extend, pop, remove, __iadd__


def test_mut_seq_append():
    """Test that optimized mutable sequences handle append correctly."""
    harness([], [append(1), len, getitem(0)])
    harness([1, 2], [append(3), len, getitem(-1)])
    harness([1], [append(2), append(3), len, getitem(slice(None))])


def test_mut_seq_clear():
    """Test that optimized mutable sequences handle clear correctly."""
    harness([], [clear(), len])
    harness([1, 2, 3], [clear(), len])
    harness([1], [clear(), len, append(100), len, getitem(0)])


def test_mut_seq_reverse():
    """Test that optimized mutable sequences handle reverse correctly."""
    harness([], [reverse(), len])
    harness([1], [reverse(), getitem(0)])
    harness([1, 2, 3], [reverse(), getitem(slice(None))])
    harness([1, 2, 3, 4, 5], [reverse(), getitem(slice(None))])


def test_mut_seq_extend():
    """Test that optimized mutable sequences handle extend correctly."""
    harness([], [extend([1, 2, 3]), len, getitem(slice(None))])
    harness([1], [extend([2, 3]), len, getitem(slice(None))])
    harness([1, 2], [extend([]), len])


def test_mut_seq_pop():
    """Test that optimized mutable sequences handle pop correctly."""
    harness([1, 2, 3], [pop(), len, getitem(slice(None))])
    harness([1, 2, 3], [pop(0), len, getitem(slice(None))])
    harness([1, 2, 3], [pop(1), len, getitem(slice(None))])
    harness([1, 2, 3], [pop(-1), len])

    # Pop from empty
    harness([], [pop()])

    # Pop out of bounds
    harness([1, 2], [pop(10)])


def test_mut_seq_remove():
    """Test that optimized mutable sequences handle remove correctly."""
    harness([1, 2, 3], [remove(1), len, getitem(slice(None))])
    harness([1, 2, 3], [remove(2), len, getitem(slice(None))])
    harness([1, 2, 1], [remove(1), len, getitem(slice(None))])

    # Remove non-existent
    harness([1, 2, 3], [remove(100)])

    # Remove from empty
    harness([], [remove(1)])


def test_mut_seq_iadd():
    """Test that optimized mutable sequences handle __iadd__ correctly."""
    harness([], [iadd([1, 2, 3]), len, getitem(slice(None))])
    harness([1], [iadd([2, 3]), len, getitem(slice(None))])
    harness([1, 2], [iadd([]), len])


# Tests for overflow scenarios: internal_sizes with various sizing configurations


def test_mut_seq_overflow_initial():
    """Test that optimized mutable sequences handle initial overflow correctly."""
    # Seed has more elements than internal_size - test multiple sizes at once
    harness(
        [1, 2, 3, 4, 5],
        [len, getitem(0), getitem(-1), getitem(slice(1, 4))],
        internal_sizes=[2, 3, 5],
    )
    harness(
        [1, 2, 3, 4, 5],
        [len, getitem(slice(None, None, -1))],
        internal_sizes=[1, 2, 4],
    )


def test_mut_seq_overflow_setitem():
    """Test that optimized mutable sequences handle setitem in overflow correctly."""
    harness(
        [1, 2, 3, 4, 5],
        [setitem(0, 100), getitem(0)],
        internal_sizes=[2, 3],
    )
    harness(
        [1, 2, 3, 4, 5],
        [setitem(-1, 100), getitem(-1)],
        internal_sizes=[2, 3],
    )
    harness(
        [1, 2, 3, 4, 5],
        [setitem(slice(1, 3), [10, 20, 30]), len],
        internal_sizes=[2, 4],
    )


def test_mut_seq_overflow_delitem():
    """Test that optimized mutable sequences handle delitem in overflow correctly."""
    harness(
        [1, 2, 3, 4, 5],
        [delitem(0), len, getitem(slice(None))],
        internal_sizes=[2, 3, 4],
    )
    harness(
        [1, 2, 3, 4, 5],
        [delitem(slice(0, 3)), len, getitem(slice(None))],
        internal_sizes=[2, 3],
    )


def test_mut_seq_overflow_insert():
    """Test that optimized mutable sequences handle insert in overflow correctly."""
    harness(
        [1, 2, 3, 4, 5],
        [insert(0, 100), len, getitem(0)],
        internal_sizes=[2, 3],
    )
    harness(
        [1, 2, 3, 4, 5],
        [insert(3, 100), len],
        internal_sizes=[2, 3, 4],
    )


def test_mut_seq_overflow_append():
    """Test that optimized mutable sequences handle append in overflow correctly."""
    harness(
        [1, 2, 3, 4, 5],
        [append(6), len, getitem(-1)],
        internal_sizes=[2, 3, 5],
    )


def test_mut_seq_overflow_extend():
    """Test that optimized mutable sequences handle extend in overflow correctly."""
    harness(
        [1, 2, 3, 4, 5],
        [extend([6, 7, 8]), len, getitem(slice(None))],
        internal_sizes=[2, 3],
    )


def test_mut_seq_overflow_pop():
    """Test that optimized mutable sequences handle pop in overflow correctly."""
    harness(
        [1, 2, 3, 4, 5],
        [pop(), len, getitem(slice(None))],
        internal_sizes=[2, 3, 4],
    )
    harness(
        [1, 2, 3, 4, 5],
        [pop(0), len, getitem(slice(None))],
        internal_sizes=[2, 3],
    )


def test_mut_seq_overflow_remove():
    """Test that optimized mutable sequences handle remove in overflow correctly."""
    harness(
        [1, 2, 3, 4, 5],
        [remove(3), len, getitem(slice(None))],
        internal_sizes=[2, 3, 4],
    )


def test_mut_seq_overflow_clear():
    """Test that optimized mutable sequences handle clear in overflow correctly."""
    harness([1, 2, 3, 4, 5], [clear(), len], internal_sizes=[2, 3])


def test_mut_seq_overflow_reverse():
    """Test that optimized mutable sequences handle reverse in overflow correctly."""
    harness(
        [1, 2, 3, 4, 5],
        [reverse(), getitem(slice(None))],
        internal_sizes=[2, 3, 4],
    )


def test_mut_seq_overflow_recovery():
    """Test that optimized mutable sequences recover from overflow when elements are removed."""
    # Start in overflow, delete elements to fit within slots, verify behavior
    harness(
        [1, 2, 3, 4, 5],
        [delitem(slice(2, 5)), len, getitem(slice(None)), append(100), len],
        internal_sizes=[3, 4],
    )

    harness(
        [1, 2, 3, 4, 5],
        [pop(), pop(), pop(), len, getitem(slice(None))],
        internal_sizes=[2, 3, 4],
    )


def test_mut_seq_growth_into_overflow():
    """Test that optimized mutable sequences transition to overflow on growth."""
    # Start within slots, grow past internal_size
    harness(
        [1, 2],
        [append(3), append(4), append(5), len, getitem(slice(None))],
        internal_sizes=[2, 3, 4],
    )
    harness(
        [1],
        [extend([2, 3, 4, 5]), len, getitem(slice(None))],
        internal_sizes=[2, 3],
    )
    harness(
        [],
        [iadd([1, 2, 3, 4, 5]), len, getitem(slice(None))],
        internal_sizes=[2, 3],
    )


def test_mut_seq_underflow():
    """Test that optimized mutable sequences with extra capacity work correctly."""
    # internal_size > len(seed), elements fit in slots with room to spare
    harness([1, 2], [len, getitem(0), getitem(1), append(3), len], internal_sizes=[3, 4, 5])
    harness([1], [insert(0, 0), insert(2, 2), len, getitem(slice(None))], internal_sizes=[3, 4, 5])
