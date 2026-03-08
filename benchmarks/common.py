"""Shared benchmark infrastructure for creating and running benchmark suites."""

import inspect
from collections.abc import Callable, Set
from dataclasses import dataclass, field
from typing import Generic, Iterable, TypeVar

import pytest

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
    extra_params: list[tuple[str, list]] = field(default_factory=list)


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
            ns[op.name] = self._make_bench_fn(op)

    def _make_bench_fn(self, op: BenchmarkOperation) -> Callable:
        extra_names = [name for name, _ in op.extra_params]
        rounds = self.rounds
        iterations = self.iterations

        def bench_fn(benchmark, case, **_extra):
            extra_args = [_extra[name] for name in extra_names]
            run = op.fn(case, *extra_args)
            benchmark.pedantic(run, rounds=rounds, iterations=iterations)

        bench_fn.__name__ = op.name

        if extra_names:
            params = [
                inspect.Parameter("benchmark", inspect.Parameter.POSITIONAL_OR_KEYWORD),
                inspect.Parameter("case", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            ] + [
                inspect.Parameter(name, inspect.Parameter.POSITIONAL_OR_KEYWORD)
                for name in extra_names
            ]
            bench_fn.__signature__ = inspect.Signature(params)

        bench_fn = pytest.mark.parametrize("case", self.cases)(bench_fn)
        for param_name, param_values in op.extra_params:
            bench_fn = pytest.mark.parametrize(param_name, param_values)(bench_fn)

        return bench_fn
