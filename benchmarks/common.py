"""Shared benchmark infrastructure for creating and running benchmark suites."""

from collections.abc import Callable, Set
from dataclasses import dataclass
from typing import Generic, Iterable, TypeVar

C = TypeVar("C", bound=Set)

ROUNDS = 200000
ITERATIONS = 10


@dataclass
class BenchmarkCase(Generic[C]):
    key: str
    size: int
    factory: Callable[[int], Callable[[C], C]]
    seed: Callable[[int], Iterable]


def instance_from_case(case: BenchmarkCase) -> Set:
    cls = case.factory(case.size)
    s = set(case.seed(case.size))
    return cls(s)


@dataclass
class BenchmarkOperation:
    name: str
    fn: Callable

    def __call__(self, cases: list, rounds: int, iterations: int):
        return self.fn(cases, rounds, iterations)


class BenchSuite:
    """Declarative benchmark suite that registers pytest benchmark functions into a module namespace."""

    def __init__(
        self,
        rounds: int,
        iterations: int,
        cases: list,
        bench: list[BenchmarkOperation],
    ):
        self.rounds = rounds
        self.iterations = iterations
        self.cases = cases
        self.bench = bench

    def register(self, ns: dict) -> None:
        """Generate and inject pytest benchmark functions into the given namespace (pass globals())."""
        for op in self.bench:
            ns[op.name] = op(self.cases, self.rounds, self.iterations)
