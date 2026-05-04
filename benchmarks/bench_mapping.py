from collections.abc import Callable, Mapping, MutableMapping
from types import MappingProxyType

from benchmarks.common import BenchmarkCase, benchmark_suite, MAX_FIXTURE_SIZE, ROUNDS, ITERATIONS
from benchmarks import mapping_ops
from opticol.factory import create_mapping_class, create_mut_mapping_class


def _mapping_maker(i: int) -> Callable[[], dict[int, int]]:
    return lambda: dict(zip(range(i), range(i)))


library_immutable_cases: list[BenchmarkCase[Mapping]] = [
    BenchmarkCase(f"mapping_immutable_{i}", create_mapping_class(i), _mapping_maker(i))
    for i in range(1, MAX_FIXTURE_SIZE)
]

library_mutable_cases: list[BenchmarkCase[MutableMapping]] = [
    BenchmarkCase(f"mapping_mutable_{i}", create_mut_mapping_class(i), _mapping_maker(i))
    for i in range(1, MAX_FIXTURE_SIZE)
]

builtin_immutable_cases: list[BenchmarkCase[Mapping]] = [
    BenchmarkCase(f"mappingproxy_{i}", MappingProxyType, _mapping_maker(i))
    for i in range(1, MAX_FIXTURE_SIZE)
]

builtin_mutable_cases: list[BenchmarkCase[MutableMapping]] = [
    BenchmarkCase(f"dict_{i}", dict, _mapping_maker(i)) for i in range(1, MAX_FIXTURE_SIZE)
]


def _bench_immutable(cases: list[BenchmarkCase]) -> None:
    benchmark_suite(
        iterations=ITERATIONS,
        rounds=ROUNDS,
        cases=cases,
        bench=[mapping_ops.init, mapping_ops.getitem, mapping_ops.iter_, mapping_ops.len_],
        ns=globals(),
    )


def _bench_mutable(cases: list[BenchmarkCase]) -> None:
    benchmark_suite(
        iterations=ITERATIONS,
        rounds=ROUNDS,
        cases=cases,
        bench=[
            mapping_ops.init,
            mapping_ops.getitem,
            mapping_ops.iter_,
            mapping_ops.len_,
            mapping_ops.setitem,
            mapping_ops.delitem,
        ],
        ns=globals(),
    )


_bench_immutable(library_immutable_cases)
_bench_immutable(builtin_immutable_cases)
_bench_mutable(library_mutable_cases)
_bench_mutable(builtin_mutable_cases)
