from collections.abc import Callable, Set
from dataclasses import dataclass
import itertools
import random
from typing import Generic, Iterable, MutableSet, TypeVar, cast
import pytest
from opticol.factory import create_mut_set_class, create_set_class

C = TypeVar("C", covariant=True, bound=Set)


@dataclass
class BenchmarkCase(Generic[C]):
    key: str
    size: int
    factory: Callable[[int], Callable[[C], C]]
    seed: Callable[[int], Iterable]


MAX_FIXTURE_SIZE = 10
ITERATIONS = 20
ROUNDS = 200000

immutable_set_cases = [
    pytest.param(BenchmarkCase[Set]("immutable", i, create_set_class, range), id=f"immutable_{i}")
    for i in range(1, MAX_FIXTURE_SIZE)
]
mutable_set_cases = [
    pytest.param(
        BenchmarkCase[MutableSet]("mutable", i, create_mut_set_class, range), id=f"mutable_{i}"
    )
    for i in range(1, MAX_FIXTURE_SIZE)
]
all_cases = [*immutable_set_cases, *mutable_set_cases]


def instance_from_case[S: Set](case: BenchmarkCase[S]) -> S:
    cls = case.factory(case.size)
    s: S = cast(S, set(case.seed(case.size)))
    instance = cls(s)
    return instance


@pytest.mark.parametrize("case", all_cases)
def bench_init(benchmark, case: BenchmarkCase[MutableSet]):
    c = create_set_class(case.size)
    seed = set(range(case.size))

    def run():
        c(seed)


    benchmark.pedantic(run, rounds=ROUNDS, iterations=ITERATIONS)


@pytest.mark.parametrize("hit_density", [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99])
@pytest.mark.parametrize("case", all_cases)
def bench_contains(benchmark, case: BenchmarkCase[Set], hit_density: float):
    optimized = instance_from_case(case)

    buffer = list(range(int(len(optimized) / hit_density)))
    random.shuffle(buffer)
    values = itertools.cycle(buffer)

    def run():
        next(values) in optimized

    benchmark.pedantic(run, rounds=ROUNDS, iterations=ITERATIONS)


@pytest.mark.parametrize("case", all_cases)
def bench_iter(benchmark, case: BenchmarkCase[Set]):
    optimized = instance_from_case(case)

    def run():
        [el for el in optimized]

    benchmark.pedantic(run, rounds=ROUNDS, iterations=ITERATIONS)


@pytest.mark.parametrize("case", all_cases)
def bench_len(benchmark, case: BenchmarkCase[Set]):
    optimized = instance_from_case(case)

    def run():
        len(optimized)

    benchmark.pedantic(run, rounds=ROUNDS, iterations=ITERATIONS)
