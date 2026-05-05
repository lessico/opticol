from collections.abc import Callable, MutableSet, Set

from benchmarks.common import BenchmarkCase, benchmark_suite, MAX_FIXTURE_SIZE, ROUNDS, ITERATIONS
from benchmarks import set_ops
from opticol.factory import create_set_class, create_mut_set_class


def _set_maker(i: int) -> Callable[[], set[int]]:
    return lambda: set(range(i))


library_immutable_cases: list[BenchmarkCase[Set]] = [
    BenchmarkCase(f"set_immutable_{i}", create_set_class(i), _set_maker(i))
    for i in range(1, MAX_FIXTURE_SIZE)
]

library_mutable_cases: list[BenchmarkCase[MutableSet]] = [
    BenchmarkCase(f"set_mutable_{i}", create_mut_set_class(i), _set_maker(i))
    for i in range(1, MAX_FIXTURE_SIZE)
]

builtin_immutable_cases: list[BenchmarkCase[Set]] = [
    BenchmarkCase(f"frozenset_{i}", frozenset, _set_maker(i)) for i in range(1, MAX_FIXTURE_SIZE)
]

builtin_mutable_cases: list[BenchmarkCase[MutableSet]] = [
    BenchmarkCase(f"set_{i}", set, _set_maker(i)) for i in range(1, MAX_FIXTURE_SIZE)
]


def _bench_immutable(cases: list[BenchmarkCase]) -> None:
    benchmark_suite(
        iterations=ITERATIONS,
        rounds=ROUNDS,
        cases=cases,
        bench=[set_ops.init, set_ops.contains, set_ops.iter_, set_ops.len_],
        ns=globals(),
    )


def _bench_mutable(cases: list[BenchmarkCase]) -> None:
    benchmark_suite(
        iterations=ITERATIONS,
        rounds=ROUNDS,
        cases=cases,
        bench=[
            set_ops.init,
            set_ops.contains,
            set_ops.iter_,
            set_ops.len_,
            set_ops.add,
            set_ops.discard,
        ],
        ns=globals(),
    )


_bench_immutable(library_immutable_cases)
_bench_immutable(builtin_immutable_cases)
_bench_mutable(library_mutable_cases)
_bench_mutable(builtin_mutable_cases)
