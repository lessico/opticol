from collections.abc import Set

from benchmarks.common import BenchmarkCase, bench_suite, MAX_FIXTURE_SIZE, ROUNDS, ITERATIONS
from benchmarks import set_ops
from opticol.factory import create_set_class

cases = [
    BenchmarkCase[Set](f"immutable_{i}", create_set_class(i), lambda: set(range(i)))
    for i in range(1, MAX_FIXTURE_SIZE)
]

bench_suite(
    iterations=ITERATIONS,
    rounds=ROUNDS,
    cases=cases,
    bench=[set_ops.init, set_ops.contains, set_ops.iter_, set_ops.len_],
    ns=globals(),
)
