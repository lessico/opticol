"""Shared benchmark infrastructure for creating and running benchmark suites."""

import inspect
from collections.abc import Callable, Set
from dataclasses import dataclass, field
from typing import Generic, Iterable, Optional, TypeVar

import pytest

C = TypeVar("C", bound=Set)

ITERATIONS = 10
ROUNDS = 200000

@dataclass
class BenchmarkCase(Generic[C]):
    key: str
    size: int
    factory: Callable[[int], Callable[[C], C]]
    seed: Callable[[int], Iterable]
    display_id: Optional[str] = field(default=None)

    def __post_init__(self) -> None:
        if self.display_id is None:
            self.display_id = f"{self.key}_{self.size}"

def instance_from_case(case: BenchmarkCase) -> Set:
    cls = case.factory(case.size)
    s = set(case.seed(case.size))
    return cls(s)


class BenchmarkOperation:
    def __init__(self, key: str, fn: Callable):
        self.key = key
        self.fn = fn
        self._extra_params: dict[str, list] = {}

    def with_params(self, **kwargs: list) -> "BenchmarkOperation":
        """Return a new BenchmarkOperation with the given parameter values set or overridden."""
        op = BenchmarkOperation(self.key, self.fn)
        op._extra_params = {**self._extra_params, **kwargs}
        return op


class BenchSuite:
    """Declarative benchmark suite that registers pytest benchmark functions into a module namespace."""

    def __init__(
        self,
        *,
        iterations: int,
        rounds: int,
        cases: list,
        bench: list[BenchmarkOperation],
    ):
        self.rounds = rounds
        self.iterations = iterations
        self.cases = cases
        self.bench = bench

    def register(self, ns: dict) -> None:
        """Generate and inject pytest benchmark functions into the given namespace (pass globals())."""
        seen_keys: set[str] = set()
        for op in self.bench:
            if op.key in seen_keys:
                raise ValueError(f"Duplicate BenchmarkOperation key: '{op.key}'")
            seen_keys.add(op.key)

        parameterized_cases = [
            pytest.param(case, id=case.display_id) if isinstance(case, BenchmarkCase) else case
            for case in self.cases
        ]

        for op in self.bench:
            ns[f"bench_{op.key}"] = self._make_bench_fn(op, parameterized_cases)

    def _make_bench_fn(self, op: BenchmarkOperation, parameterized_cases: list) -> Callable:
        extra_names = list(op._extra_params.keys())
        rounds = self.rounds
        iterations = self.iterations

        def bench_fn(benchmark, case, **_extra):
            extra_args = [_extra[name] for name in extra_names]
            run = op.fn(case, *extra_args)
            benchmark.pedantic(run, rounds=rounds, iterations=iterations)

        bench_fn.__name__ = f"bench_{op.key}"

        if extra_names:
            params = [
                inspect.Parameter("benchmark", inspect.Parameter.POSITIONAL_OR_KEYWORD),
                inspect.Parameter("case", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            ] + [
                inspect.Parameter(name, inspect.Parameter.POSITIONAL_OR_KEYWORD)
                for name in extra_names
            ]
            setattr(bench_fn, "__signature__", inspect.Signature(params))

        bench_fn = pytest.mark.parametrize("case", parameterized_cases)(bench_fn)
        for param_name, param_values in op._extra_params.items():
            bench_fn = pytest.mark.parametrize(param_name, param_values)(bench_fn)

        return bench_fn
