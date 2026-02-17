"""Test the memory optimized MutableMapping implementation for equivalence with builtins."""

from collections.abc import Callable, MutableMapping
from typing import Any

from opticol.factory import create_mut_mapping_class
from tests import mapping, shared
from tests.mapping import (
    getitem,
    contains,
    get,
    keys,
    values,
    items,
    eq_op,
    setitem,
    delitem,
    pop,
    popitem,
    clear,
    update,
    setdefault,
)


def harness[K, V](
    seed: MutableMapping[K, V],
    ops: list[Callable[[MutableMapping], Any]],
    internal_sizes: list[int] | None = None,
) -> None:
    """
    The wrapper around the main test harness implementation.

    Checks that for a given seed or start MutableMapping value, the set of provided operations
    have the same result on the optimized variants and the builtin dict implementation.

    Args:
        seed: The MutableMapping value to create the various implementations with for testing.
        ops: The operations whose behavior needs to be validated across builtins and optimized
            variants.
        internal_sizes: The internal slot sizes for the optimized collections. When None, uses
            [len(seed)] for exact size matching. When specified, creates an optimized collection
            for each size, allowing testing of overflow behavior (size < len(seed)) or growth
            into available slots (size > len(seed)).
    """
    sizes = internal_sizes if internal_sizes is not None else [len(seed)]
    factories: list[shared.Factory[MutableMapping[K, V]]] = [dict] + [
        create_mut_mapping_class(size) for size in sizes
    ]
    shared.harness(seed, factories, ops, mapping.eq, mapping.eq_op_result)


# Tests for abstract methods: __getitem__, __iter__, __len__


def test_mut_mapping_len():
    """Test that optimized mutable mappings have the same len semantics as dict."""
    harness({}, [len])
    harness({"a": 1}, [len])
    harness({"a": 1, "b": 2}, [len])
    harness({"a": 1, "b": 2, "c": 3}, [len])


def test_mut_mapping_getitem():
    """Test that optimized mutable mappings handle getitem correctly."""
    harness({"a": 1, "b": 2, "c": 3}, [getitem("a"), getitem("b"), getitem("c")])

    # Missing key should raise KeyError
    harness({"a": 1}, [getitem("b")])
    harness({}, [getitem("a")])


def test_mut_mapping_getitem_various_key_types():
    """Test that optimized mutable mappings handle various key types correctly."""
    harness({1: "one", 2: "two"}, [getitem(1), getitem(2)])
    harness({(1, 2): "tuple_key"}, [getitem((1, 2))])
    harness({None: "none_value"}, [getitem(None)])
    harness({True: "true", False: "false"}, [getitem(True), getitem(False)])


def test_mut_mapping_iter():
    """Test that optimized mutable mappings have the same iter semantics as dict."""
    harness({}, [iter])
    harness({"a": 1}, [iter])
    harness({"a": 1, "b": 2, "c": 3}, [iter])


# Tests for mixin methods: __contains__, keys, values, items, get, __eq__/__ne__


def test_mut_mapping_contains():
    """Test that optimized mutable mappings have the same contains semantics as dict."""
    harness({"a": 1, "b": 2}, [contains("a"), contains("b"), contains("c", False)])
    harness({}, [contains("a", False)])
    harness({1: "one"}, [contains(1), contains("1", False)])
    harness({None: "value"}, [contains(None)])


def test_mut_mapping_keys():
    """Test that optimized mutable mappings have the same keys semantics as dict."""
    harness({}, [keys()])
    harness({"a": 1}, [keys()])
    harness({"a": 1, "b": 2, "c": 3}, [keys()])


def test_mut_mapping_values():
    """Test that optimized mutable mappings have the same values semantics as dict."""
    harness({}, [values()])
    harness({"a": 1}, [values()])
    harness({"a": 1, "b": 2, "c": 3}, [values()])


def test_mut_mapping_values_duplicates():
    """Test that optimized mutable mappings handle duplicate values correctly."""
    harness({"a": 1, "b": 1, "c": 1}, [values()])
    harness({"a": None, "b": None}, [values()])


def test_mut_mapping_items():
    """Test that optimized mutable mappings have the same items semantics as dict."""
    harness({}, [items()])
    harness({"a": 1}, [items()])
    harness({"a": 1, "b": 2, "c": 3}, [items()])


def test_mut_mapping_get():
    """Test that optimized mutable mappings have the same get semantics as dict."""
    harness({"a": 1, "b": 2}, [get("a"), get("b"), get("c")])
    harness({"a": 1}, [get("a", 100), get("b", 100)])
    harness({}, [get("a"), get("a", "default")])


def test_mut_mapping_get_none_value():
    """Test that optimized mutable mappings handle get with None values correctly."""
    harness({"a": None}, [get("a"), get("a", "default"), get("b")])


def test_mut_mapping_eq():
    """Test that optimized mutable mappings have the same equality semantics as dict."""
    harness({"a": 1, "b": 2}, [eq_op({"a": 1, "b": 2}), eq_op({"a": 1}, False)])
    harness({}, [eq_op({}), eq_op({"a": 1}, False)])
    harness({"a": 1}, [eq_op({"a": 1}), eq_op({"a": 2}, False), eq_op({"b": 1}, False)])


# Tests for MutableMapping abstract methods: __setitem__, __delitem__


def test_mut_mapping_setitem():
    """Test that optimized mutable mappings handle __setitem__ correctly."""
    # Add new key
    harness({"a": 1}, [setitem("b", 2), len, getitem("b")])

    # Overwrite existing key
    harness({"a": 1, "b": 2}, [setitem("a", 100), getitem("a")])

    # Add to empty mapping
    harness({}, [setitem("a", 1), len, getitem("a")])

    # Multiple setitems
    harness({}, [setitem("a", 1), setitem("b", 2), setitem("c", 3), len, keys()])


def test_mut_mapping_setitem_various_key_types():
    """Test that optimized mutable mappings handle setitem with various key types."""
    harness({}, [setitem(1, "one"), setitem(2, "two"), len, getitem(1)])
    harness({}, [setitem((1, 2), "tuple"), getitem((1, 2))])
    harness({}, [setitem(None, "none"), getitem(None)])
    harness({}, [setitem(True, "true"), getitem(True)])


def test_mut_mapping_delitem():
    """Test that optimized mutable mappings handle __delitem__ correctly."""
    # Delete existing key
    harness({"a": 1, "b": 2, "c": 3}, [delitem("b"), len, contains("b", False)])
    harness({"a": 1, "b": 2}, [delitem("a"), len, getitem("b")])

    # Delete last remaining key
    harness({"a": 1}, [delitem("a"), len])

    # Delete missing key should raise KeyError
    harness({"a": 1}, [delitem("b")])

    # Delete from empty
    harness({}, [delitem("a")])


# Tests for MutableMapping mixin methods: pop, popitem, clear, update, setdefault


def test_mut_mapping_pop():
    """Test that optimized mutable mappings handle pop correctly."""
    # Pop existing key
    harness({"a": 1, "b": 2, "c": 3}, [pop("b"), len, contains("b", False)])
    harness({"a": 1, "b": 2}, [pop("a"), len])

    # Pop missing key should raise KeyError
    harness({"a": 1}, [pop("b")])

    # Pop from empty should raise KeyError
    harness({}, [pop("a")])

    # Pop with default for missing key
    harness({"a": 1}, [pop("b", 999)])
    harness({}, [pop("a", None)])

    # Pop with default for existing key (returns value, not default)
    harness({"a": 1, "b": 2}, [pop("a", 999), len])


def test_mut_mapping_popitem():
    """Test that optimized mutable mappings handle popitem correctly."""
    # Pop from single-element mapping
    harness({"a": 1}, [popitem(), len])

    # Pop from multi-element mapping
    harness({"a": 1, "b": 2}, [popitem(), len])
    harness({"a": 1, "b": 2, "c": 3}, [popitem(), popitem(), len])

    # Pop from empty should raise KeyError
    harness({}, [popitem()])


def test_mut_mapping_clear():
    """Test that optimized mutable mappings handle clear correctly."""
    # Clear empty
    harness({}, [clear(), len])

    # Clear non-empty
    harness({"a": 1, "b": 2, "c": 3}, [clear(), len])

    # Clear then add
    harness({"a": 1}, [clear(), len, setitem("x", 100), len, getitem("x")])


def test_mut_mapping_update():
    """Test that optimized mutable mappings handle update correctly."""
    # Update with new keys
    harness({"a": 1}, [update({"b": 2, "c": 3}), len, getitem("b"), getitem("c")])

    # Update with overlapping keys
    harness({"a": 1, "b": 2}, [update({"b": 20, "c": 30}), len, getitem("b"), getitem("c")])

    # Update empty mapping
    harness({}, [update({"a": 1, "b": 2}), len, getitem("a")])

    # Update with empty dict (no-op)
    harness({"a": 1}, [update({}), len, getitem("a")])


def test_mut_mapping_setdefault():
    """Test that optimized mutable mappings handle setdefault correctly."""
    # Key exists: returns existing value, does not modify
    harness({"a": 1, "b": 2}, [setdefault("a", 100), getitem("a")])

    # Key missing: inserts default and returns it
    harness({"a": 1}, [setdefault("b", 2), len, getitem("b")])

    # Key missing with no explicit default: inserts None
    harness({"a": 1}, [setdefault("b"), len, getitem("b")])

    # Setdefault on empty mapping
    harness({}, [setdefault("a", 1), len, getitem("a")])


# Tests for overflow scenarios: internal_sizes with various sizing configurations


def test_mut_mapping_overflow_initial():
    """Test that optimized mutable mappings handle initial overflow correctly."""
    harness(
        {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        [len, getitem("a"), getitem("e"), contains("c"), keys(), values(), items()],
        internal_sizes=[2, 3, 5],
    )
    harness(
        {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        [len, iter, get("c"), get("f", 0)],
        internal_sizes=[1, 2, 4],
    )


def test_mut_mapping_overflow_setitem():
    """Test that optimized mutable mappings handle setitem in overflow correctly."""
    # Add new key while already overflowed
    harness(
        {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        [setitem("f", 6), len, getitem("f")],
        internal_sizes=[2, 3],
    )
    # Overwrite existing key while overflowed
    harness(
        {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        [setitem("c", 100), getitem("c")],
        internal_sizes=[2, 3],
    )


def test_mut_mapping_overflow_delitem():
    """Test that optimized mutable mappings handle delitem in overflow correctly."""
    harness(
        {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        [delitem("c"), len, contains("c", False)],
        internal_sizes=[2, 3, 4],
    )
    # Delete missing key in overflow
    harness(
        {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        [delitem("z")],
        internal_sizes=[2, 3],
    )


def test_mut_mapping_overflow_pop():
    """Test that optimized mutable mappings handle pop in overflow correctly."""
    harness(
        {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        [pop("c"), len, contains("c", False)],
        internal_sizes=[2, 3, 4],
    )
    # Pop with default in overflow
    harness(
        {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        [pop("z", 0)],
        internal_sizes=[2, 3],
    )


def test_mut_mapping_overflow_clear():
    """Test that optimized mutable mappings handle clear in overflow correctly."""
    harness(
        {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        [clear(), len],
        internal_sizes=[2, 3],
    )


def test_mut_mapping_overflow_update():
    """Test that optimized mutable mappings handle update in overflow correctly."""
    harness(
        {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        [update({"f": 6, "g": 7}), len, getitem("f")],
        internal_sizes=[2, 3],
    )
    # Update with overlapping keys in overflow
    harness(
        {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        [update({"a": 100, "e": 500}), getitem("a"), getitem("e")],
        internal_sizes=[2, 3],
    )


def test_mut_mapping_overflow_setdefault():
    """Test that optimized mutable mappings handle setdefault in overflow correctly."""
    # Key exists in overflow
    harness(
        {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        [setdefault("c", 999), getitem("c")],
        internal_sizes=[2, 3],
    )
    # Key missing in overflow
    harness(
        {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        [setdefault("f", 6), len, getitem("f")],
        internal_sizes=[2, 3],
    )


# Tests for overflow recovery, growth into overflow, and underflow


def test_mut_mapping_overflow_recovery():
    """Test that optimized mutable mappings recover from overflow when entries are removed."""
    # Start in overflow, delete entries to fit within slots, verify behavior
    harness(
        {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        [delitem("c"), delitem("d"), delitem("e"), len, getitem("a"), getitem("b")],
        internal_sizes=[3, 4],
    )

    harness(
        {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        [pop("a"), pop("b"), pop("c"), len, keys()],
        internal_sizes=[2, 3, 4],
    )


def test_mut_mapping_growth_into_overflow():
    """Test that optimized mutable mappings transition to overflow on growth."""
    # Start within slots, grow past internal_size
    harness(
        {"a": 1, "b": 2},
        [setitem("c", 3), setitem("d", 4), setitem("e", 5), len, keys()],
        internal_sizes=[2, 3, 4],
    )
    harness(
        {"a": 1},
        [update({"b": 2, "c": 3, "d": 4, "e": 5}), len, getitem("e")],
        internal_sizes=[2, 3],
    )
    harness(
        {},
        [setitem("a", 1), setitem("b", 2), setitem("c", 3), len, keys()],
        internal_sizes=[2, 3],
    )


def test_mut_mapping_underflow():
    """Test that optimized mutable mappings with extra capacity work correctly."""
    # internal_size > len(seed), elements fit in slots with room to spare
    harness(
        {"a": 1, "b": 2},
        [len, getitem("a"), getitem("b"), setitem("c", 3), len],
        internal_sizes=[3, 4, 5],
    )
    harness(
        {"a": 1},
        [setitem("b", 2), setitem("c", 3), len, keys()],
        internal_sizes=[3, 4, 5],
    )


# Integrated scenario tests with mixed operations


def test_mut_mapping_scenario_build_and_query():
    """Test building a mapping from scratch with setitem and querying with various read ops."""
    harness(
        {},
        [
            setitem("x", 10),
            setitem("y", 20),
            setitem("z", 30),
            len,
            getitem("x"),
            getitem("y"),
            getitem("z"),
            contains("x"),
            contains("w", False),
            get("y"),
            get("w", 0),
            keys(),
            values(),
            items(),
        ],
        internal_sizes=[3, 5],
    )


def test_mut_mapping_scenario_modify_and_verify():
    """Test modifying an existing mapping with overwrites, deletes, and pops."""
    harness(
        {"a": 1, "b": 2, "c": 3, "d": 4},
        [
            setitem("a", 100),
            delitem("b"),
            pop("c"),
            len,
            getitem("a"),
            contains("b", False),
            contains("c", False),
            getitem("d"),
            keys(),
            values(),
            items(),
        ],
    )


def test_mut_mapping_scenario_clear_and_rebuild():
    """Test clearing a mapping and rebuilding it from scratch."""
    harness(
        {"a": 1, "b": 2, "c": 3},
        [
            clear(),
            len,
            setitem("x", 10),
            setitem("y", 20),
            len,
            getitem("x"),
            getitem("y"),
            contains("a", False),
            keys(),
        ],
    )


def test_mut_mapping_scenario_mixed_operations():
    """Test interleaving various mutable and read operations."""
    harness(
        {"a": 1, "b": 2},
        [
            setitem("c", 3),
            update({"d": 4, "e": 5}),
            len,
            setdefault("f", 6),
            setdefault("a", 999),
            getitem("a"),
            getitem("f"),
            pop("b"),
            delitem("c"),
            len,
            keys(),
            values(),
            items(),
        ],
    )
