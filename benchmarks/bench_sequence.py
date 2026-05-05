from collections.abc import Callable, MutableSequence, Sequence

from benchmarks.common import BenchmarkCase, benchmark_suite, MAX_FIXTURE_SIZE, ROUNDS, ITERATIONS
from benchmarks import sequence_ops
from opticol.factory import create_seq_class, create_mut_seq_class


def _seq_maker(i: int) -> Callable[[], list[int]]:
    return lambda: list(range(i))


library_immutable_cases: list[BenchmarkCase[Sequence]] = [
    BenchmarkCase(f"sequence_immutable_{i}", create_seq_class(i), _seq_maker(i))
    for i in range(1, MAX_FIXTURE_SIZE)
]

library_mutable_cases: list[BenchmarkCase[MutableSequence]] = [
    BenchmarkCase(f"sequence_mutable_{i}", create_mut_seq_class(i), _seq_maker(i))
    for i in range(1, MAX_FIXTURE_SIZE)
]

builtin_immutable_cases: list[BenchmarkCase[Sequence]] = [
    BenchmarkCase(f"tuple_{i}", tuple, _seq_maker(i)) for i in range(1, MAX_FIXTURE_SIZE)
]

builtin_mutable_cases: list[BenchmarkCase[MutableSequence]] = [
    BenchmarkCase(f"list_{i}", list, _seq_maker(i)) for i in range(1, MAX_FIXTURE_SIZE)
]


def _bench_immutable(cases: list[BenchmarkCase]) -> None:
    benchmark_suite(
        iterations=ITERATIONS,
        rounds=ROUNDS,
        cases=cases,
        bench=[sequence_ops.init, sequence_ops.getitem, sequence_ops.len_],
        ns=globals(),
    )


def _bench_mutable(cases: list[BenchmarkCase]) -> None:
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


_bench_immutable(library_immutable_cases)
_bench_immutable(builtin_immutable_cases)
_bench_mutable(library_mutable_cases)
_bench_mutable(builtin_mutable_cases)
