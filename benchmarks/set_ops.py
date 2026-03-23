"""Shared benchmark operation descriptors for Set and MutableSet benchmarks."""

from collections.abc import Callable, MutableSet, Set
import itertools
import math
import random

from benchmarks.common import BenchmarkCase, BenchmarkOperation, proportional_indexer, instance_from_case, HIT_DENSITIES

def _init(case: BenchmarkCase[Set]) -> Callable[[], None]:
    cls = case.cls
    seed = case.seed()

    def run():
        cls(seed)

    return run


def _contains(case: BenchmarkCase[Set], hit_density: float) -> Callable[[], None]:
    optimized = instance_from_case(case)
    values = proportional_indexer(optimized, hit_density)

    def run():
        next(values) in optimized

    return run


def _iter(case: BenchmarkCase[Set]) -> Callable[[], None]:
    optimized = instance_from_case(case)

    def run():
        for _ in optimized:
            pass

    return run


def _len(case: BenchmarkCase[Set]) -> Callable[[], None]:
    optimized = instance_from_case(case)

    def run():
        len(optimized)

    return run


def _add(case: BenchmarkCase[MutableSet], hit_density: float) -> Callable[[], None]:
    s = case.seed()
    values = proportional_indexer(s, hit_density)

    def run():
        instance = case.cls(s)
        instance.add(next(values))

    return run


def _discard(case: BenchmarkCase[MutableSet], hit_density: float) -> Callable[[], None]:
    s = case.seed()
    values = proportional_indexer(s, hit_density)

    def run():
        instance = case.cls(s)
        instance.discard(next(values))

    return run


init = BenchmarkOperation(key="init", fn=_init)
contains = BenchmarkOperation(key="contains", fn=_contains).with_params(hit_density=HIT_DENSITIES)
iter_ = BenchmarkOperation(key="iter", fn=_iter)
len_ = BenchmarkOperation(key="len", fn=_len)
add = BenchmarkOperation(key="add", fn=_add).with_params(hit_density=HIT_DENSITIES)
discard = BenchmarkOperation(key="discard", fn=_discard).with_params(hit_density=HIT_DENSITIES)
