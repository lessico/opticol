"""Equality checks and operation wrappers for Mapping and MutableMapping tests."""

from collections.abc import (
    Iterator,
    ItemsView,
    KeysView,
    Mapping,
    MutableMapping,
    ValuesView,
)
from typing import Any, Callable


def eq(m1: Mapping, m2: Mapping) -> bool:
    """
    Return if two mappings are identical at the Mapping interface level.

    Args:
        m1: One of the mappings to compare for equality.
        m2: The other mapping to compare for equality.

    Returns:
        True if the two mappings are identical and False otherwise.
    """
    if len(m1) != len(m2):
        return False

    for key in m1:
        if key not in m2:
            return False
        if m1[key] != m2[key]:
            return False

    return True


type MappingRelatedView = ItemsView | KeysView | ValuesView


def eq_view[V: MappingRelatedView](v1: V, v2: V) -> bool:
    """
    Checks if two views created from a map are identical.

    Args:
        v1: The first view to compare for equality.
        v2: The second view t compare for equality.

    Returns:
        True if the two views are identical.
    """
    if len(v1) != len(v2):
        return False

    for obj in v1:
        if obj not in v2:
            return False

    return True


def eq_op_result(first: Any, second: Any, materialized_cache: dict[Iterator, list]) -> bool:
    """
    Checks if the result of two Mapping operations are identical.

    The results are obtained if the Mapping operation succeeds and does not raise an error.
    Mapping operation here refers to those operations defined on the ABC collection documentation
    as required to implement, and mixins.

    Based on this documentation, the possible results from a Mapping operation are an Iterator,
    a KeysView, ValuesView, ItemsView, a value from the mapping, a boolean, or None.

    Args:
        first: The first result to compare.
        second: The second result to compare.
        materialized_cache: The per harness cache of iterators to their in-memory materialized
            version.

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

    if (
        (isinstance(first, KeysView) and isinstance(second, KeysView))
        or (isinstance(first, ItemsView) and isinstance(second, ItemsView))
        or (isinstance(first, ValuesView) and isinstance(second, ValuesView))
    ):
        return eq_view(first, second)

    # The results of the operations are values, booleans, tuples, or None.
    return first == second


# Operation wrappers for Mapping methods


def getitem[K, V](key: K) -> Callable[[Mapping[K, V]], V]:
    """Create a callable which wraps getitem and calls it on the given Mapping."""
    return lambda m: m[key]


def contains[K](key: K, expected: bool = True) -> Callable[[Mapping[K, Any]], bool]:
    """Create a callable which wraps __contains__ and calls it on the given Mapping."""
    return lambda m: (key in m) == expected


def get[K, V](key: K, default: V | None = None) -> Callable[[Mapping[K, V]], V | None]:
    """Create a callable which wraps get and calls it on the given Mapping."""
    return lambda m: m.get(key, default)


def keys[K]() -> Callable[[Mapping[K, Any]], KeysView[K]]:
    """Create a callable which wraps keys and calls it on the given Mapping."""
    return lambda m: m.keys()


def values[V]() -> Callable[[Mapping[Any, V]], ValuesView[V]]:
    """Create a callable which wraps values and calls it on the given Mapping."""
    return lambda m: m.values()


def items[K, V]() -> Callable[[Mapping[K, V]], ItemsView[K, V]]:
    """Create a callable which wraps items and calls it on the given Mapping."""
    return lambda m: m.items()


def eq_op[K, V](other: Mapping[K, V], expected: bool = True) -> Callable[[Mapping[K, V]], bool]:
    """Create a callable which wraps __eq__/__ne__ and calls it on the given Mapping."""
    return lambda m: (m == other) == expected


# Operation wrappers for MutableMapping methods


def setitem[K, V](key: K, value: V) -> Callable[[MutableMapping[K, V]], None]:
    """Create a callable which wraps __setitem__ and calls it on the given MutableMapping."""

    def op(m):
        m[key] = value

    return op


def delitem[K](key: K) -> Callable[[MutableMapping[K, Any]], None]:
    """Create a callable which wraps __delitem__ and calls it on the given MutableMapping."""

    def op(m):
        del m[key]

    return op


def pop[K, V](key: K, *args: V) -> Callable[[MutableMapping[K, V]], V]:
    """Create a callable which wraps pop and calls it on the given MutableMapping.

    An optional default value can be provided as a positional argument, matching the
    signature of MutableMapping.pop(key[, default]).
    """
    return lambda m: m.pop(key, *args)


def popitem[K, V]() -> Callable[[MutableMapping[K, V]], tuple[K, V]]:
    """Create a callable which wraps popitem and calls it on the given MutableMapping."""
    return lambda m: m.popitem()


def clear() -> Callable[[MutableMapping], None]:
    """Create a callable which wraps clear and calls it on the given MutableMapping."""

    def op(m):
        m.clear()

    return op


def update[K, V](
    other: Mapping[K, V] | None = None, **kwargs: V
) -> Callable[[MutableMapping[K, V]], None]:
    """Create a callable which wraps update and calls it on the given MutableMapping."""

    def op(m):
        m.update(other or {}, **kwargs)

    return op


def setdefault[K](key: K, default: Any = None) -> Callable[[MutableMapping[K, Any]], Any]:
    """Create a callable which wraps setdefault and calls it on the given MutableMapping."""
    return lambda m: m.setdefault(key, default)
