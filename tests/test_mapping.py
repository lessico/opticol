"""Test the memory optimized Mapping implementation for equivalence with builtins."""

from collections.abc import Callable, Mapping
from typing import Any

from opticol.factory import create_mapping_class
from tests import mapping, shared
from tests.mapping import getitem, contains, get, keys, values, items, eq_op


def harness[K, V](
    seed: Mapping[K, V],
    ops: list[Callable[[Mapping], Any]],
) -> None:
    """
    The wrapper around the main test harness implementation.

    Checks that for a given seed or start Mapping value, the set of provided operations have the
    same result on the optimized and the builtin Mapping implementations.

    Args:
        seed: The Mapping value to create the various implementations with for testing.
        ops: The operations whose behavior needs to be validated across builtins and optimized
            variants.
    """
    factories = [dict, create_mapping_class(len(seed))]
    shared.harness(seed, factories, ops, mapping.eq, mapping.eq_op_result)


# Tests for abstract methods: __getitem__, __iter__, __len__


def test_mapping_len():
    """Test that optimized mappings have the same len semantics as dict."""
    harness({}, [len])
    harness({"a": 1}, [len])
    harness({"a": 1, "b": 2}, [len])
    harness({"a": 1, "b": 2, "c": 3}, [len])


def test_mapping_getitem():
    """Test that optimized mappings handle getitem correctly."""
    harness({"a": 1, "b": 2, "c": 3}, [getitem("a"), getitem("b"), getitem("c")])

    # Missing key should raise KeyError
    harness({"a": 1}, [getitem("b")])
    harness({}, [getitem("a")])


def test_mapping_getitem_various_key_types():
    """Test that optimized mappings handle various key types correctly."""
    harness({1: "one", 2: "two"}, [getitem(1), getitem(2)])
    harness({(1, 2): "tuple_key"}, [getitem((1, 2))])
    harness({None: "none_value"}, [getitem(None)])
    harness({True: "true", False: "false"}, [getitem(True), getitem(False)])


def test_mapping_iter():
    """Test that optimized mappings have the same iter semantics as dict."""
    harness({}, [iter])
    harness({"a": 1}, [iter])
    harness({"a": 1, "b": 2, "c": 3}, [iter])


# Tests for mixin methods: __contains__, keys, values, items, get, __eq__/__ne__


def test_mapping_contains():
    """Test that optimized mappings have the same contains semantics as dict."""
    harness({"a": 1, "b": 2}, [contains("a"), contains("b"), contains("c", False)])
    harness({}, [contains("a", False)])
    harness({1: "one"}, [contains(1), contains("1", False)])
    harness({None: "value"}, [contains(None)])


def test_mapping_keys():
    """Test that optimized mappings have the same keys semantics as dict."""
    harness({}, [keys()])
    harness({"a": 1}, [keys()])
    harness({"a": 1, "b": 2, "c": 3}, [keys()])


def test_mapping_values():
    """Test that optimized mappings have the same values semantics as dict."""
    harness({}, [values()])
    harness({"a": 1}, [values()])
    harness({"a": 1, "b": 2, "c": 3}, [values()])


def test_mapping_values_duplicates():
    """Test that optimized mappings handle duplicate values correctly."""
    harness({"a": 1, "b": 1, "c": 1}, [values()])
    harness({"a": None, "b": None}, [values()])


def test_mapping_items():
    """Test that optimized mappings have the same items semantics as dict."""
    harness({}, [items()])
    harness({"a": 1}, [items()])
    harness({"a": 1, "b": 2, "c": 3}, [items()])


def test_mapping_get():
    """Test that optimized mappings have the same get semantics as dict."""
    harness({"a": 1, "b": 2}, [get("a"), get("b"), get("c")])
    harness({"a": 1}, [get("a", 100), get("b", 100)])
    harness({}, [get("a"), get("a", "default")])


def test_mapping_get_none_value():
    """Test that optimized mappings handle get with None values correctly."""
    harness({"a": None}, [get("a"), get("a", "default"), get("b")])


def test_mapping_eq():
    """Test that optimized mappings have the same equality semantics as dict."""
    harness({"a": 1, "b": 2}, [eq_op({"a": 1, "b": 2}), eq_op({"a": 1}, False)])
    harness({}, [eq_op({}), eq_op({"a": 1}, False)])
    harness({"a": 1}, [eq_op({"a": 1}), eq_op({"a": 2}, False), eq_op({"b": 1}, False)])


def test_mapping_eq_different_order():
    """Test that mapping equality is order-independent."""
    harness({"a": 1, "b": 2}, [eq_op({"b": 2, "a": 1})])
    harness({"x": 10, "y": 20, "z": 30}, [eq_op({"z": 30, "x": 10, "y": 20})])


# Scenario tests with mixed operations


def test_mapping_larger_mappings():
    """Test that optimized mappings work correctly with 4 and 5 element counts."""
    harness(
        {"a": 1, "b": 2, "c": 3, "d": 4},
        [
            len,
            getitem("a"),
            getitem("d"),
            contains("b"),
            contains("e", False),
            get("c"),
            get("e", 0),
            keys(),
            values(),
            items(),
            iter,
        ],
    )

    harness(
        {1: "a", 2: "b", 3: "c", 4: "d", 5: "e"},
        [
            len,
            getitem(1),
            getitem(5),
            contains(3),
            keys(),
            values(),
            items(),
        ],
    )


def test_mapping_mixed_key_value_types():
    """Test that optimized mappings handle mixed key and value types correctly."""
    harness(
        {"str": 1, 2: "int_key", None: [1, 2, 3]},
        [
            len,
            getitem("str"),
            getitem(2),
            getitem(None),
            contains("str"),
            contains(2),
            contains(None),
            contains("missing", False),
            get("str"),
            get(2),
            get(None),
            keys(),
            values(),
            items(),
        ],
    )
