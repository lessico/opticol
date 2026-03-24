from collections.abc import Callable, Mapping

from benchmarks.common import BenchmarkCase, benchmark_suite, MAX_FIXTURE_SIZE, ROUNDS, ITERATIONS
from benchmarks import mapping_ops
from opticol.factory import create_mapping_class


def _mapping_maker(i: int) -> Callable[[], dict[int, int]]:
    return lambda: dict(zip(range(i), range(i)))


cases = [
    BenchmarkCase[Mapping](f"immutable_{i}", create_mapping_class(i), _mapping_maker(i))
    for i in range(1, MAX_FIXTURE_SIZE)
]

benchmark_suite(
    iterations=ITERATIONS,
    rounds=ROUNDS,
    cases=cases,
    bench=[mapping_ops.init, mapping_ops.getitem, mapping_ops.iter_, mapping_ops.len_],
    ns=globals(),
)
