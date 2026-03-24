from collections.abc import Callable, MutableMapping

from benchmarks.common import BenchmarkCase, benchmark_suite, MAX_FIXTURE_SIZE, ROUNDS, ITERATIONS
from benchmarks import mapping_ops
from opticol.factory import create_mut_mapping_class


def _mapping_maker(i: int) -> Callable[[], dict[int, int]]:
    return lambda: dict(zip(range(i), range(i)))


cases = [
    BenchmarkCase[MutableMapping](f"mutable_{i}", create_mut_mapping_class(i), _mapping_maker(i))
    for i in range(1, MAX_FIXTURE_SIZE)
]

benchmark_suite(
    iterations=ITERATIONS,
    rounds=ROUNDS,
    cases=cases,
    bench=[
        mapping_ops.getitem,
        mapping_ops.iter_,
        mapping_ops.len_,
        mapping_ops.setitem,
        mapping_ops.delitem,
    ],
    ns=globals(),
)
