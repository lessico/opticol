from collections.abc import Callable, Set

from benchmarks.common import BenchmarkCase, benchmark_suite, MAX_FIXTURE_SIZE, ROUNDS, ITERATIONS
from benchmarks import set_ops
from opticol.factory import create_set_class


def _set_maker(i: int) -> Callable[[], set[int]]:
    return lambda: set(range(i))


cases = [
    BenchmarkCase[Set](f"set_immutable_{i}", create_set_class(i), _set_maker(i))
    for i in range(1, MAX_FIXTURE_SIZE)
]

benchmark_suite(
    iterations=ITERATIONS,
    rounds=ROUNDS,
    cases=cases,
    bench=[set_ops.init, set_ops.contains, set_ops.iter_, set_ops.len_],
    ns=globals(),
)
