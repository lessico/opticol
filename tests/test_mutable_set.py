"""Test the memory optimized MutableSet implementation for equivalence with builtins."""

from collections.abc import Callable, MutableSet
from typing import Any

from opticol.factory import create_mut_set_class
from tests import set as set_, shared
from tests.set import (
    contains,
    isdisjoint,
    le,
    lt,
    ge,
    gt,
    eq_op,
    and_op,
    or_op,
    sub,
    xor,
    add,
    discard,
    remove,
    pop,
    clear,
    ior,
    iand,
    ixor,
    isub,
)


def harness[T](
    seed: MutableSet[T],
    ops: list[Callable[[MutableSet], Any]],
    internal_sizes: list[int] | None = None,
) -> None:
    """
    The wrapper around the main test harness implementation.

    Checks that for a given seed or start MutableSet value, the set of provided operations
    have the same result on the optimized variants and the builtin set implementation.

    Args:
        seed: The MutableSet value to create the various implementations with for testing.
        ops: The operations whose behavior needs to be validated across builtins and optimized
            variants.
        internal_sizes: The internal slot sizes for the optimized collections. When None, uses
            [len(seed)] for exact size matching. When specified, creates an optimized collection
            for each size, allowing testing of overflow behavior (size < len(seed)) or growth
            into available slots (size > len(seed)).
    """
    sizes = internal_sizes if internal_sizes is not None else [len(seed)]
    factories: list[shared.Factory[MutableSet[T]]] = [set] + [
        create_mut_set_class(size) for size in sizes
    ]
    shared.harness(seed, factories, ops, set_.eq, set_.eq_op_result)


# Tests for abstract methods: __contains__, __iter__, __len__


def test_mut_set_len():
    """Test that optimized mutable sets have the same len semantics as set."""
    harness(set(), [len])
    harness({1}, [len])
    harness({1, 2}, [len])
    harness({1, 2, 3}, [len])


def test_mut_set_contains():
    """Test that optimized mutable sets have the same contains semantics as set."""
    harness({1, 2, 3}, [contains(1), contains(2), contains(3), contains(4, False)])
    harness(set(), [contains(1, False)])
    harness({None}, [contains(None), contains(1, False)])


def test_mut_set_contains_various_types():
    """Test that optimized mutable sets handle various element types correctly."""
    harness({1, "a", (1, 2)}, [contains(1), contains("a"), contains((1, 2)), contains("b", False)])
    harness({True, False}, [contains(True), contains(False), contains(1)])


def test_mut_set_iter():
    """Test that optimized mutable sets have the same iter semantics as set."""
    harness(set(), [iter])
    harness({1}, [iter])
    harness({1, 2, 3}, [iter])


# Tests for mixin methods: isdisjoint


def test_mut_set_isdisjoint():
    """Test that optimized mutable sets have the same isdisjoint semantics as set."""
    harness({1, 2, 3}, [isdisjoint({4, 5, 6}), isdisjoint({3, 4, 5}), isdisjoint(set())])
    harness(set(), [isdisjoint(set()), isdisjoint({1, 2})])
    harness({1}, [isdisjoint({1}), isdisjoint({2})])


# Tests for comparison operations: __le__, __lt__, __ge__, __gt__, __eq__


def test_mut_set_le():
    """Test that optimized mutable sets have the same __le__ (issubset) semantics as set."""
    harness({1, 2}, [le({1, 2, 3}), le({1, 2}), le({1}, False)])
    harness(set(), [le(set()), le({1})])
    harness({1, 2, 3}, [le({1, 2, 3}), le({1, 2}, False)])


def test_mut_set_lt():
    """Test that optimized mutable sets have the same __lt__ (proper subset) semantics as set."""
    harness({1, 2}, [lt({1, 2, 3}), lt({1, 2}, False), lt({1}, False)])
    harness(set(), [lt(set(), False), lt({1})])
    harness({1}, [lt({1, 2}), lt({1}, False)])


def test_mut_set_ge():
    """Test that optimized mutable sets have the same __ge__ (issuperset) semantics as set."""
    harness({1, 2, 3}, [ge({1, 2}), ge({1, 2, 3}), ge({1, 2, 3, 4}, False)])
    harness(set(), [ge(set()), ge({1}, False)])
    harness({1, 2}, [ge({1}), ge({1, 2}), ge({1, 2, 3}, False)])


def test_mut_set_gt():
    """Test that optimized mutable sets have the same __gt__ (proper superset) semantics as set."""
    harness({1, 2, 3}, [gt({1, 2}), gt({1, 2, 3}, False), gt({1, 2, 3, 4}, False)])
    harness(set(), [gt(set(), False)])
    harness({1, 2}, [gt({1}), gt({1, 2}, False)])


def test_mut_set_eq():
    """Test that optimized mutable sets have the same equality semantics as set."""
    harness({1, 2, 3}, [eq_op({1, 2, 3}), eq_op({1, 2}, False), eq_op({1, 2, 3, 4}, False)])
    harness(set(), [eq_op(set()), eq_op({1}, False)])
    harness({1}, [eq_op({1}), eq_op({2}, False)])


# Tests for set operations: __and__, __or__, __sub__, __xor__


def test_mut_set_and():
    """Test that optimized mutable sets have the same __and__ (intersection) semantics as set."""
    harness({1, 2, 3}, [and_op({2, 3, 4}), and_op({4, 5, 6}), and_op(set())])
    harness(set(), [and_op(set()), and_op({1, 2})])
    harness({1, 2}, [and_op({1, 2}), and_op({1})])


def test_mut_set_or():
    """Test that optimized mutable sets have the same __or__ (union) semantics as set."""
    harness({1, 2}, [or_op({3, 4}), or_op({2, 3}), or_op(set())])
    harness(set(), [or_op(set()), or_op({1, 2})])
    harness({1}, [or_op({1}), or_op({2})])


def test_mut_set_sub():
    """Test that optimized mutable sets have the same __sub__ (difference) semantics as set."""
    harness({1, 2, 3}, [sub({2}), sub({1, 2, 3}), sub({4, 5}), sub(set())])
    harness(set(), [sub(set()), sub({1, 2})])
    harness({1, 2}, [sub({1}), sub({2}), sub({1, 2})])


def test_mut_set_xor():
    """Test that optimized mutable sets have the same __xor__ (symmetric_difference) semantics as set."""
    harness({1, 2, 3}, [xor({2, 3, 4}), xor({1, 2, 3}), xor(set())])
    harness(set(), [xor(set()), xor({1, 2})])
    harness({1, 2}, [xor({2, 3}), xor({1, 2})])


# Tests for MutableSet abstract methods: add, discard


def test_mut_set_add():
    """Test that optimized mutable sets handle add correctly."""
    # Add new element
    harness({1, 2}, [add(3), len, contains(3)])

    # Add duplicate (no-op)
    harness({1, 2, 3}, [add(2), len, contains(2)])

    # Add duplicate when free slots are available (no-op)
    harness({1, 2}, [add(1), len, contains(1)], internal_sizes=[3, 4])

    # Add to empty
    harness(set(), [add(1), len, contains(1)])

    # Multiple adds
    harness(set(), [add(1), add(2), add(3), len])


def test_mut_set_discard():
    """Test that optimized mutable sets handle discard correctly."""
    # Discard existing element
    harness({1, 2, 3}, [discard(2), len, contains(2, False)])

    # Discard missing element (no-op, no error)
    harness({1, 2, 3}, [discard(4), len])

    # Discard from empty (no-op, no error)
    harness(set(), [discard(1), len])

    # Discard last element
    harness({1}, [discard(1), len])


# Tests for MutableSet mixin methods: remove, pop, clear, __ior__, __iand__, __ixor__, __isub__


def test_mut_set_remove():
    """Test that optimized mutable sets handle remove correctly."""
    # Remove existing element
    harness({1, 2, 3}, [remove(2), len, contains(2, False)])
    harness({1, 2}, [remove(1), len, contains(1, False)])

    # Remove last element
    harness({1}, [remove(1), len])

    # Remove missing element should raise KeyError
    harness({1, 2, 3}, [remove(4)])

    # Remove from empty should raise KeyError
    harness(set(), [remove(1)])


def test_mut_set_pop():
    """Test that optimized mutable sets handle pop correctly.

    Since set.pop() returns an arbitrary element, tests use single-element sets where the
    result is unambiguous, and empty sets where both implementations raise KeyError.
    """
    # Pop from single-element set (unambiguous)
    harness({1}, [pop(), len])

    # Pop from empty should raise KeyError
    harness(set(), [pop()])


def test_mut_set_clear():
    """Test that optimized mutable sets handle clear correctly."""
    # Clear empty
    harness(set(), [clear(), len])

    # Clear non-empty
    harness({1, 2, 3}, [clear(), len])

    # Clear then add
    harness({1, 2}, [clear(), len, add(100), len, contains(100)])


def test_mut_set_ior():
    """Test that optimized mutable sets handle __ior__ (|=) correctly."""
    # Union-assign with new elements
    harness({1, 2}, [ior({3, 4}), len, contains(3), contains(4)])

    # Union-assign with overlapping elements
    harness({1, 2, 3}, [ior({2, 3, 4}), len, contains(4)])

    # Union-assign with empty set (no-op)
    harness({1, 2}, [ior(set()), len])

    # Union-assign on empty set
    harness(set(), [ior({1, 2, 3}), len, contains(1)])


def test_mut_set_iand():
    """Test that optimized mutable sets handle __iand__ (&=) correctly."""
    # Intersect-assign narrowing
    harness({1, 2, 3}, [iand({2, 3, 4}), len, contains(1, False), contains(2), contains(3)])

    # Intersect-assign no overlap (empties the set)
    harness({1, 2, 3}, [iand({4, 5, 6}), len])

    # Intersect-assign with empty (empties the set)
    harness({1, 2, 3}, [iand(set()), len])

    # Intersect-assign with superset (no-op)
    harness({1, 2}, [iand({1, 2, 3}), len, contains(1), contains(2)])


def test_mut_set_ixor():
    """Test that optimized mutable sets handle __ixor__ (^=) correctly."""
    # Symmetric difference with partial overlap
    harness({1, 2, 3}, [ixor({2, 3, 4}), len, contains(1), contains(4), contains(2, False)])

    # Symmetric difference with identical set (empties)
    harness({1, 2, 3}, [ixor({1, 2, 3}), len])

    # Symmetric difference with empty set (no-op)
    harness({1, 2}, [ixor(set()), len, contains(1)])

    # Symmetric difference on empty set
    harness(set(), [ixor({1, 2}), len, contains(1)])


def test_mut_set_isub():
    """Test that optimized mutable sets handle __isub__ (-=) correctly."""
    # Difference-assign partial overlap
    harness({1, 2, 3}, [isub({2, 3}), len, contains(1), contains(2, False)])

    # Difference-assign no overlap (no-op)
    harness({1, 2, 3}, [isub({4, 5}), len])

    # Difference-assign with empty (no-op)
    harness({1, 2}, [isub(set()), len, contains(1)])

    # Difference-assign removing all elements
    harness({1, 2, 3}, [isub({1, 2, 3}), len])

    # Difference-assign on empty set
    harness(set(), [isub({1, 2}), len])


# Tests for overflow scenarios: internal_sizes with various sizing configurations


def test_mut_set_overflow_initial():
    """Test that optimized mutable sets handle initial overflow correctly."""
    harness(
        {1, 2, 3, 4, 5},
        [len, contains(1), contains(5), contains(6, False), iter],
        internal_sizes=[2, 3, 5],
    )
    harness(
        {1, 2, 3, 4, 5},
        [len, isdisjoint({6, 7}), le({1, 2, 3, 4, 5, 6}), and_op({2, 3})],
        internal_sizes=[1, 2, 4],
    )


def test_mut_set_overflow_add():
    """Test that optimized mutable sets handle add in overflow correctly."""
    harness(
        {1, 2, 3, 4, 5},
        [add(6), len, contains(6)],
        internal_sizes=[2, 3],
    )
    # Add duplicate in overflow (no-op)
    harness(
        {1, 2, 3, 4, 5},
        [add(3), len],
        internal_sizes=[2, 3],
    )


def test_mut_set_overflow_discard():
    """Test that optimized mutable sets handle discard in overflow correctly."""
    harness(
        {1, 2, 3, 4, 5},
        [discard(3), len, contains(3, False)],
        internal_sizes=[2, 3, 4],
    )
    # Discard missing in overflow
    harness(
        {1, 2, 3, 4, 5},
        [discard(6), len],
        internal_sizes=[2, 3],
    )


def test_mut_set_overflow_remove():
    """Test that optimized mutable sets handle remove in overflow correctly."""
    harness(
        {1, 2, 3, 4, 5},
        [remove(3), len, contains(3, False)],
        internal_sizes=[2, 3, 4],
    )
    # Remove missing in overflow should raise KeyError
    harness(
        {1, 2, 3, 4, 5},
        [remove(6)],
        internal_sizes=[2, 3],
    )


def test_mut_set_overflow_clear():
    """Test that optimized mutable sets handle clear in overflow correctly."""
    harness(
        {1, 2, 3, 4, 5},
        [clear(), len],
        internal_sizes=[2, 3],
    )


def test_mut_set_overflow_ior():
    """Test that optimized mutable sets handle __ior__ (|=) in overflow correctly."""
    harness(
        {1, 2, 3, 4, 5},
        [ior({6, 7}), len, contains(6)],
        internal_sizes=[2, 3],
    )
    # |= with overlapping in overflow
    harness(
        {1, 2, 3, 4, 5},
        [ior({4, 5, 6}), len, contains(6)],
        internal_sizes=[2, 3],
    )


def test_mut_set_overflow_iand():
    """Test that optimized mutable sets handle __iand__ (&=) in overflow correctly."""
    harness(
        {1, 2, 3, 4, 5},
        [iand({2, 3, 4}), len, contains(1, False), contains(2)],
        internal_sizes=[2, 3],
    )


def test_mut_set_overflow_isub():
    """Test that optimized mutable sets handle __isub__ (-=) in overflow correctly."""
    harness(
        {1, 2, 3, 4, 5},
        [isub({1, 2, 3}), len, contains(1, False), contains(4)],
        internal_sizes=[2, 3],
    )


# Tests for overflow recovery, growth into overflow, and underflow


def test_mut_set_overflow_recovery():
    """Test that optimized mutable sets recover from overflow when elements are removed."""
    # Start in overflow, discard elements to fit within slots, verify behavior
    harness(
        {1, 2, 3, 4, 5},
        [discard(3), discard(4), discard(5), len, contains(1), contains(2)],
        internal_sizes=[3, 4],
    )

    harness(
        {1, 2, 3, 4, 5},
        [remove(1), remove(2), remove(3), len],
        internal_sizes=[2, 3, 4],
    )


def test_mut_set_growth_into_overflow():
    """Test that optimized mutable sets transition to overflow on growth."""
    # Start within slots, grow past internal_size
    harness(
        {1, 2},
        [add(3), add(4), add(5), len],
        internal_sizes=[2, 3, 4],
    )
    harness(
        {1},
        [ior({2, 3, 4, 5}), len, contains(5)],
        internal_sizes=[2, 3],
    )
    harness(
        set(),
        [add(1), add(2), add(3), add(4), add(5), len],
        internal_sizes=[2, 3],
    )


def test_mut_set_underflow():
    """Test that optimized mutable sets with extra capacity work correctly."""
    # internal_size > len(seed), elements fit in slots with room to spare
    harness(
        {1, 2},
        [len, contains(1), contains(2), add(3), len],
        internal_sizes=[3, 4, 5],
    )
    harness(
        {1},
        [add(2), add(3), len, contains(3)],
        internal_sizes=[3, 4, 5],
    )


# Integrated scenario tests with mixed operations


def test_mut_set_scenario_build_and_query():
    """Test building a set from scratch with add and querying with various read ops."""
    harness(
        set(),
        [
            add(10),
            add(20),
            add(30),
            len,
            contains(10),
            contains(20),
            contains(30),
            contains(40, False),
            isdisjoint({40, 50}),
            le({10, 20, 30, 40}),
            ge({10, 20}),
            and_op({20, 30, 40}),
            or_op({40}),
            sub({10}),
            iter,
        ],
        internal_sizes=[3, 5],
    )


def test_mut_set_scenario_modify_and_verify():
    """Test modifying an existing set with add, discard, and remove."""
    harness(
        {1, 2, 3, 4},
        [
            add(5),
            discard(2),
            remove(3),
            len,
            contains(1),
            contains(2, False),
            contains(3, False),
            contains(4),
            contains(5),
            eq_op({1, 4, 5}),
        ],
    )


def test_mut_set_scenario_clear_and_rebuild():
    """Test clearing a set and rebuilding it from scratch."""
    harness(
        {1, 2, 3},
        [
            clear(),
            len,
            add(10),
            add(20),
            len,
            contains(10),
            contains(20),
            contains(1, False),
        ],
    )


def test_mut_set_scenario_mixed_operations():
    """Test interleaving various mutable and read operations."""
    harness(
        {1, 2, 3},
        [
            add(4),
            ior({5, 6}),
            len,
            isub({1, 2}),
            len,
            contains(1, False),
            contains(3),
            iand({3, 4, 5, 10}),
            len,
            ixor({4, 7}),
            len,
            contains(4, False),
            contains(7),
            iter,
        ],
    )
