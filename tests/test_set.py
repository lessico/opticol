"""Test the memory optimized Set implementation for equivalence with builtins."""

from collections.abc import Callable, Set
from typing import Any

from opticol.factory import create_set_class
from tests import set as set_, shared
from tests.set import contains, isdisjoint, le, lt, ge, gt, eq_op, and_op, or_op, sub, xor


def harness[T](
    seed: Set[T],
    ops: list[Callable[[Set], Any]],
) -> None:
    """
    The wrapper around the main test harness implementation.

    Checks that for a given seed or start Set value, the set of provided operations have the
    same result on the optimized and the builtin Set implementations.

    Args:
        seed: The Set value to create the various implementations with for testing.
        ops: The operations whose behavior needs to be validated across builtins and optimized
            variants.
    """
    factories = [set, frozenset, create_set_class(len(seed))]
    shared.harness(seed, factories, ops, set_.eq, set_.eq_op_result)


# Tests for abstract methods: __contains__, __iter__, __len__


def test_set_len():
    """Test that optimized sets have the same len semantics as frozenset."""
    harness(set(), [len])
    harness({1}, [len])
    harness({1, 2}, [len])
    harness({1, 2, 3}, [len])


def test_set_contains():
    """Test that optimized sets have the same contains semantics as frozenset."""
    harness({1, 2, 3}, [contains(1), contains(2), contains(3), contains(4, False)])
    harness(set(), [contains(1, False)])
    harness({None}, [contains(None), contains(1, False)])


def test_set_contains_various_types():
    """Test that optimized sets handle various element types correctly."""
    harness({1, "a", (1, 2)}, [contains(1), contains("a"), contains((1, 2)), contains("b", False)])
    harness({True, False}, [contains(True), contains(False), contains(1)])


def test_set_iter():
    """Test that optimized sets have the same iter semantics as frozenset."""
    harness(set(), [iter])
    harness({1}, [iter])
    harness({1, 2, 3}, [iter])


# Tests for mixin methods: isdisjoint


def test_set_isdisjoint():
    """Test that optimized sets have the same isdisjoint semantics as frozenset."""
    harness({1, 2, 3}, [isdisjoint({4, 5, 6}), isdisjoint({3, 4, 5}), isdisjoint(set())])
    harness(set(), [isdisjoint(set()), isdisjoint({1, 2})])
    harness({1}, [isdisjoint({1}), isdisjoint({2})])


# Tests for comparison operations: __le__, __lt__, __ge__, __gt__, __eq__


def test_set_le():
    """Test that optimized sets have the same __le__ (issubset) semantics as frozenset."""
    harness({1, 2}, [le({1, 2, 3}), le({1, 2}), le({1}, False)])
    harness(set(), [le(set()), le({1})])
    harness({1, 2, 3}, [le({1, 2, 3}), le({1, 2}, False)])


def test_set_lt():
    """Test that optimized sets have the same __lt__ (proper subset) semantics as frozenset."""
    harness({1, 2}, [lt({1, 2, 3}), lt({1, 2}, False), lt({1}, False)])
    harness(set(), [lt(set(), False), lt({1})])
    harness({1}, [lt({1, 2}), lt({1}, False)])


def test_set_ge():
    """Test that optimized sets have the same __ge__ (issuperset) semantics as frozenset."""
    harness({1, 2, 3}, [ge({1, 2}), ge({1, 2, 3}), ge({1, 2, 3, 4}, False)])
    harness(set(), [ge(set()), ge({1}, False)])
    harness({1, 2}, [ge({1}), ge({1, 2}), ge({1, 2, 3}, False)])


def test_set_gt():
    """Test that optimized sets have the same __gt__ (proper superset) semantics as frozenset."""
    harness({1, 2, 3}, [gt({1, 2}), gt({1, 2, 3}, False), gt({1, 2, 3, 4}, False)])
    harness(set(), [gt(set(), False)])
    harness({1, 2}, [gt({1}), gt({1, 2}, False)])


def test_set_eq():
    """Test that optimized sets have the same equality semantics as frozenset."""
    harness({1, 2, 3}, [eq_op({1, 2, 3}), eq_op({1, 2}, False), eq_op({1, 2, 3, 4}, False)])
    harness(set(), [eq_op(set()), eq_op({1}, False)])
    harness({1}, [eq_op({1}), eq_op({2}, False)])


# Tests for set operations: __and__, __or__, __sub__, __xor__


def test_set_and():
    """Test that optimized sets have the same __and__ (intersection) semantics as frozenset."""
    harness({1, 2, 3}, [and_op({2, 3, 4}), and_op({4, 5, 6}), and_op(set())])
    harness(set(), [and_op(set()), and_op({1, 2})])
    harness({1, 2}, [and_op({1, 2}), and_op({1})])


def test_set_or():
    """Test that optimized sets have the same __or__ (union) semantics as frozenset."""
    harness({1, 2}, [or_op({3, 4}), or_op({2, 3}), or_op(set())])
    harness(set(), [or_op(set()), or_op({1, 2})])
    harness({1}, [or_op({1}), or_op({2})])


def test_set_sub():
    """Test that optimized sets have the same __sub__ (difference) semantics as frozenset."""
    harness({1, 2, 3}, [sub({2}), sub({1, 2, 3}), sub({4, 5}), sub(set())])
    harness(set(), [sub(set()), sub({1, 2})])
    harness({1, 2}, [sub({1}), sub({2}), sub({1, 2})])


def test_set_xor():
    """Test that optimized sets have the same __xor__ (symmetric_difference) semantics as frozenset."""
    harness({1, 2, 3}, [xor({2, 3, 4}), xor({1, 2, 3}), xor(set())])
    harness(set(), [xor(set()), xor({1, 2})])
    harness({1, 2}, [xor({2, 3}), xor({1, 2})])


# Scenario tests with mixed operations


def test_set_larger_sets():
    """Test that optimized sets work correctly with 4 and 5 element counts."""
    harness(
        {1, 2, 3, 4},
        [
            len,
            contains(1),
            contains(5, False),
            isdisjoint({5, 6, 7}),
            le({1, 2, 3, 4, 5}),
            ge({1, 2}),
            and_op({2, 3, 4, 5}),
            or_op({4, 5}),
            sub({1}),
            xor({3, 4, 5}),
            iter,
        ],
    )

    harness(
        {10, 20, 30, 40, 50},
        [
            len,
            contains(30),
            isdisjoint({1, 2, 3}),
            and_op({20, 30, 60}),
            or_op({60, 70}),
        ],
    )


def test_set_mixed_element_types():
    """Test that optimized sets handle mixed element types correctly."""
    harness(
        {1, "two", (3, 4), None},
        [
            len,
            contains(1),
            contains("two"),
            contains((3, 4)),
            contains(None),
            contains("missing", False),
            isdisjoint({"other"}),
            and_op({1, "two"}),
            or_op({"five"}),
            iter,
        ],
    )


def test_set_boolean_int_equality():
    """Test that optimized sets handle True==1 and False==0 correctly."""
    # In Python, True == 1 and False == 0, so {True, 1} has only one element
    harness({True, 1}, [len, contains(True), contains(1)])
    harness({False, 0}, [len, contains(False), contains(0)])
