from collections.abc import Callable, Sequence, Set
from dataclasses import dataclass, field
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


@dataclass
class BenchmarkCaseCollection(Generic[C]):
    cases: Sequence[BenchmarkCase[C]]
    names: Sequence[str] = field(init=False)

    def __post_init__(self) -> None:
        self.names = [f"{case.key}_{case.size}" for case in self.cases]


MAX_FIXTURE_SIZE = 10
immutable_set = BenchmarkCaseCollection(
    [
        BenchmarkCase[Set]("immutable", i, create_set_class, range)
        for i in range(2, MAX_FIXTURE_SIZE)
    ]
)
mutable_set = BenchmarkCaseCollection(
    [
        BenchmarkCase[MutableSet]("mutable", i, create_mut_set_class, range)
        for i in range(1, MAX_FIXTURE_SIZE)
    ]
)
all = BenchmarkCaseCollection([*immutable_set.cases, *mutable_set.cases])


def instance_from_case[S: Set](case: BenchmarkCase[S]) -> S:
    cls = case.factory(case.size)
    s: S = cast(S, set(case.seed(case.size)))
    instance = cls(s)
    return instance


@pytest.mark.parametrize("case", all.cases, ids=all.names)
def test_bench_init(benchmark, case: BenchmarkCase[MutableSet]):
    c = create_set_class(case.size)
    seed = set(range(case.size))

    def run():
        c(seed)

    benchmark(run)


@pytest.mark.parametrize("case", all.cases, ids=all.names)
def test_bench_contains(benchmark, case: BenchmarkCase[Set]):
    optimized = instance_from_case(case)

    max = len(optimized)
    sample = random.sample(range(max * 2), 500)
    values = itertools.cycle(sample)

    def run():
        next(values) in optimized

    benchmark(run)


@pytest.mark.parametrize("case", all.cases, ids=all.names)
def test_bench_iter(benchmark, case: BenchmarkCase[Set]):
    optimized = instance_from_case(case)

    def run():
        [el for el in optimized]

    benchmark(run)


@pytest.mark.parametrize("case", all.cases, ids=all.names)
def test_bench_len(benchmark, case: BenchmarkCase[Set]):
    optimized = instance_from_case(case)

    def run():
        len(optimized)

    benchmark(run)
