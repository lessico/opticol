from fractions import Fraction
import inspect
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
import itertools
import math
import random
from typing import Any, Optional

import pytest

MAX_FIXTURE_SIZE = 10
ITERATIONS = 10
ROUNDS = 200000
HIT_DENSITIES = [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99]


@dataclass
class BenchmarkCase[C]:
    key: str
    cls: Callable[[C], C]
    seed: Callable[[], C]


def instance_from_case[C](case: BenchmarkCase[C]) -> C:
    s = case.seed()
    return case.cls(s)


def amortized_indexer[T](indices: Iterable[T], *, scale: Optional[int] = None) -> Iterator[T]:
    if scale is not None and scale <= 0:
        raise ValueError(f"scale parameter for amortized_indexer must be positive but '{scale}' was given.")

    final = []
    base = list(indices)
    n = int(len(base) / (scale or 1))

    for _ in range(n):
        copy = base[:]
        random.shuffle(copy)
        final.extend(copy)
    return itertools.cycle(final)

def proportional_indexer[T](indices: Iterable[T], hit_density: float, epsilon: float=0.01) -> Iterable:
    if hit_density > 1 or hit_density <= 0:
        raise ValueError(f"The hit_density parameter must be in the interval (0, 1] but '{hit_density}' was given.")

    l = list(indices)

    max_denom = max(1, math.ceil(1 / (hit_density * epsilon)))
    frac = Fraction(hit_density).limit_denominator(max_denom)

    g = math.gcd(frac.numerator, len(l))
    scale = int(frac.numerator // g)
    total = frac.denominator * len(l) // g
    new_object_count = total - (len(l) * scale)

    as_list: list[Any] = l * scale
    for _ in range(new_object_count):
        as_list.append(object())

    return amortized_indexer(as_list, scale=scale)




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


def benchmark_suite[C](
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

    needed = set(extra_params)
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
        ] + [inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY) for name in extra_params]
        setattr(bench_fn, "__signature__", inspect.Signature(params))

    bench_fn = pytest.mark.parametrize("case", parameterized_cases)(bench_fn)
    for name in extra_params:
        values = op._extra_params[name]
        bench_fn = pytest.mark.parametrize(name, values)(bench_fn)

    return bench_fn
