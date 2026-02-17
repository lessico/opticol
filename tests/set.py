"""Equality checks and operation wrappers for Set and MutableSet tests."""

from collections.abc import Iterator, MutableSet, Set
from typing import Any, Callable


def eq(s1: Set, s2: Set) -> bool:
    """
    Return if two sets are identical at the Set interface level.

    Args:
        s1: One of the sets to compare for equality.
        s2: The other set to compare for equality.

    Returns:
        True if the two sets are identical and False otherwise.
    """
    if len(s1) != len(s2):
        return False

    for item in s1:
        if item not in s2:
            return False

    return True


def eq_op_result(first: Any, second: Any, materialized_cache: dict[Iterator, list]) -> bool:
    """
    Checks if the result of two Set operations are identical.

    The results are obtained if the Set operation succeeds and does not raise an error.
    Set operation here refers to those operations defined on the ABC collection documentation
    as required to implement, and mixins.

    Based on this documentation, the possible results from a Set operation are an Iterator,
    another Set, or a boolean.

    Args:
        first: The first result to compare.
        second: The second result to compare.
        materialized_cache: The per harness cache of iterators to their in-memory materialized version.

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

        return set(f) == set(s)

    if isinstance(first, Set) and isinstance(second, Set):
        return eq(first, second)

    # The results of the operations are booleans.
    return first == second


# Operation wrappers for Set methods


def contains[T](item: T, expected: bool = True) -> Callable[[Set[T]], bool]:
    """Create a callable which wraps __contains__ and calls it on the given Set."""
    return lambda s: (item in s) == expected


def isdisjoint[T](other: Set[T]) -> Callable[[Set[T]], bool]:
    """Create a callable which wraps isdisjoint and calls it on the given Set."""
    return lambda s: s.isdisjoint(other)


def le[T](other: Set[T], expected: bool = True) -> Callable[[Set[T]], bool]:
    """Create a callable which wraps __le__ (issubset) and calls it on the given Set."""
    return lambda s: (s <= other) == expected


def lt[T](other: Set[T], expected: bool = True) -> Callable[[Set[T]], bool]:
    """Create a callable which wraps __lt__ (proper subset) and calls it on the given Set."""
    return lambda s: (s < other) == expected


def ge[T](other: Set[T], expected: bool = True) -> Callable[[Set[T]], bool]:
    """Create a callable which wraps __ge__ (issuperset) and calls it on the given Set."""
    return lambda s: (s >= other) == expected


def gt[T](other: Set[T], expected: bool = True) -> Callable[[Set[T]], bool]:
    """Create a callable which wraps __gt__ (proper superset) and calls it on the given Set."""
    return lambda s: (s > other) == expected


def eq_op[T](other: Set[T], expected: bool = True) -> Callable[[Set[T]], bool]:
    """Create a callable which wraps __eq__/__ne__ and calls it on the given Set."""
    return lambda s: (s == other) == expected


def and_op[T](other: Set[T]) -> Callable[[Set[T]], Set[T]]:
    """Create a callable which wraps __and__ (intersection) and calls it on the given Set."""
    return lambda s: s & other


def or_op[T](other: Set[T]) -> Callable[[Set[T]], Set[T]]:
    """Create a callable which wraps __or__ (union) and calls it on the given Set."""
    return lambda s: s | other


def sub[T](other: Set[T]) -> Callable[[Set[T]], Set[T]]:
    """Create a callable which wraps __sub__ (difference) and calls it on the given Set."""
    return lambda s: s - other


def xor[T](other: Set[T]) -> Callable[[Set[T]], Set[T]]:
    """Create a callable which wraps __xor__ (symmetric_difference) and calls it on the given Set."""
    return lambda s: s ^ other


# Operation wrappers for MutableSet methods


def add[T](value: T) -> Callable[[MutableSet[T]], None]:
    """Create a callable which wraps add and calls it on the given MutableSet."""

    def op(s):
        s.add(value)

    return op


def discard[T](value: T) -> Callable[[MutableSet[T]], None]:
    """Create a callable which wraps discard and calls it on the given MutableSet."""

    def op(s):
        s.discard(value)

    return op


def remove[T](value: T) -> Callable[[MutableSet[T]], None]:
    """Create a callable which wraps remove and calls it on the given MutableSet."""

    def op(s):
        s.remove(value)

    return op


def pop[T]() -> Callable[[MutableSet[T]], T]:
    """Create a callable which wraps pop and calls it on the given MutableSet."""
    return lambda s: s.pop()


def clear() -> Callable[[MutableSet], None]:
    """Create a callable which wraps clear and calls it on the given MutableSet."""

    def op(s):
        s.clear()

    return op


def ior[T](other: Set[T]) -> Callable[[MutableSet[T]], None]:
    """Create a callable which wraps __ior__ (|=) and calls it on the given MutableSet."""

    def op(s):
        s |= other

    return op


def iand[T](other: Set[T]) -> Callable[[MutableSet[T]], None]:
    """Create a callable which wraps __iand__ (&=) and calls it on the given MutableSet."""

    def op(s):
        s &= other

    return op


def ixor[T](other: Set[T]) -> Callable[[MutableSet[T]], None]:
    """Create a callable which wraps __ixor__ (^=) and calls it on the given MutableSet."""

    def op(s):
        s ^= other

    return op


def isub[T](other: Set[T]) -> Callable[[MutableSet[T]], None]:
    """Create a callable which wraps __isub__ (-=) and calls it on the given MutableSet."""

    def op(s):
        s -= other

    return op
