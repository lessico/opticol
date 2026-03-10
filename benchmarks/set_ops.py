"""Shared benchmark operation descriptors for Set and MutableSet benchmarks."""

from collections.abc import Callable, Set
import itertools
import random

from benchmarks.common import BenchmarkCase, BenchmarkOperation, instance_from_case

HIT_DENSITIES = [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99]


def _init(case: BenchmarkCase[Set]) -> Callable[[], None]:
    cls = case.cls
    seed = case.seed()

    def run():
        cls(seed)

    return run


def _contains(case: BenchmarkCase[Set], hit_density: float) -> Callable[[], None]:
    optimized = instance_from_case(case)
    buffer = list(range(int(len(optimized) / hit_density)))
    random.shuffle(buffer)
    values = itertools.cycle(buffer)

    def run():
        next(values) in optimized

    return run


def _iter(case: BenchmarkCase[Set]) -> Callable[[], None]:
    optimized = instance_from_case(case)

    def run():
        [el for el in optimized]

    return run


def _len(case: BenchmarkCase[Set]) -> Callable[[], None]:
    optimized = instance_from_case(case)

    def run():
        len(optimized)

    return run


init = BenchmarkOperation(key="init", fn=_init)
contains = BenchmarkOperation(key="contains", fn=_contains).with_params(hit_density=HIT_DENSITIES)
iter_ = BenchmarkOperation(key="iter", fn=_iter)
len_ = BenchmarkOperation(key="len", fn=_len)
