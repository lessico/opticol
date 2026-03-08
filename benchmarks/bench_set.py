"""Benchmarks for the memory-optimized immutable Set implementation."""

from collections.abc import Set

import pytest

from benchmarks.common import BenchmarkCase, BenchSuite, ROUNDS, ITERATIONS
from benchmarks import set_ops
from opticol.factory import create_set_class

MAX_FIXTURE_SIZE = 10

cases = [
    pytest.param(
        BenchmarkCase[Set]("immutable", i, create_set_class, range),
        id=f"immutable_{i}",
    )
    for i in range(1, MAX_FIXTURE_SIZE)
]

BenchSuite(
    rounds=ROUNDS,
    iterations=ITERATIONS,
    cases=cases,
    bench=[set_ops.init, set_ops.contains, set_ops.iter_, set_ops.len_],
).register(globals())
