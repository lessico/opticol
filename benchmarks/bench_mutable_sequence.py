from collections.abc import Callable, MutableSequence

from benchmarks.common import BenchmarkCase, benchmark_suite, MAX_FIXTURE_SIZE, ROUNDS, ITERATIONS
from benchmarks import sequence_ops
from opticol.factory import create_mut_seq_class


def _seq_maker(i: int) -> Callable[[], list[int]]:
    return lambda: list(range(i))


cases = [
    BenchmarkCase[MutableSequence](f"mutable_{i}", create_mut_seq_class(i), _seq_maker(i))
    for i in range(1, MAX_FIXTURE_SIZE)
]

benchmark_suite(
    iterations=ITERATIONS,
    rounds=ROUNDS,
    cases=cases,
    bench=[
        sequence_ops.init,
        sequence_ops.getitem,
        sequence_ops.len_,
        sequence_ops.setitem,
        sequence_ops.delitem,
        sequence_ops.insert,
    ],
    ns=globals(),
)
