import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

import pytest

C = TypeVar("C", covariant=True)

MAX_FIXTURE_SIZE = 10
ITERATIONS = 10
ROUNDS = 200000


@dataclass
class BenchmarkCase(Generic[C]):
    key: str
    cls: Callable[[C], C]
    seed: Callable[[], C]


def instance_from_case[C](case: BenchmarkCase[C]) -> C:
    s = case.seed()
    return case.cls(s)


class BenchmarkOperation:
    def __init__(self, key: str, fn: Callable[..., Callable[[], None]]):
        self.key = key
        self.fn = fn
        self._extra_params: dict[str, list] = {}

    def with_params(self, **kwargs: list) -> "BenchmarkOperation":
        op = BenchmarkOperation(self.key, self.fn)
        op._extra_params = {**self._extra_params, **kwargs}
        return op

    def with_key(self, new_key: str) -> "BenchmarkOperation":
        op = BenchmarkOperation(new_key, self.fn)
        op._extra_params = self._extra_params
        return op


def bench_suite[C](
    *,
    iterations: int,
    rounds: int,
    cases: list[BenchmarkCase[C]],
    bench: list[BenchmarkOperation],
    ns: dict[str, Any],
) -> None:
    seen_keys: set[str] = set()
    for op in bench:
        if op.key in seen_keys:
            raise ValueError(f"Duplicate BenchmarkOperation key: '{op.key}'")
        seen_keys.add(op.key)

    parameterized_cases = [pytest.param(case, id=case.key) for case in cases]

    for op in bench:
        ns[f"bench_{op.key}"] = _make_bench_fn(iterations, rounds, op, parameterized_cases)


def _make_bench_fn(
    iterations: int, rounds: int, op: BenchmarkOperation, parameterized_cases: list
) -> Callable:
    fn_params = list(inspect.signature(op.fn).parameters.keys())
    if fn_params[0] != "case":
        raise ValueError(f"Expected first parameter of benchmark operation '{op.key}' to be 'case'")

    extra_params = fn_params[1:]

    needed = set(fn_params[:1])
    provided = set(op._extra_params)
    if needed != provided:
        missing = needed - provided
        extra = provided - needed
        raise ValueError(f"Parameter mismatch for '{op.key}: missing={missing}, extra={extra}")

    def bench_fn(benchmark, case, **extra):
        extra = [extra[name] for name in extra_params]
        run = op.fn(case, *extra)
        benchmark.pedantic(run, rounds=rounds, iterations=iterations)

    bench_fn.__name__ = f"bench_{op.key}"

    if extra_params:
        params = [
            inspect.Parameter("benchmark", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter("case", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        ] + [
            inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY) for name in extra_params 
        ]
        setattr(bench_fn, "__signature__", inspect.Signature(params))

    bench_fn = pytest.mark.parametrize("case", parameterized_cases)(bench_fn)
    for name in extra_params:
        values = op._extra_params[name]
        bench_fn = pytest.mark.parametrize(name, values)(bench_fn)

    return bench_fn
