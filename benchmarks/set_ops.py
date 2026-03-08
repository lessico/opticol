"""Shared benchmark operation descriptors for Set and MutableSet benchmarks."""

import itertools
import random
from collections.abc import Set

import pytest

from benchmarks.common import BenchmarkCase, BenchmarkOperation, instance_from_case

HIT_DENSITIES = [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99]


def _init(cases: list, rounds: int, iterations: int):
    @pytest.mark.parametrize("case", cases)
    def bench_init(benchmark, case: BenchmarkCase):
        cls = case.factory(case.size)
        seed = set(case.seed(case.size))

        def run():
            cls(seed)

        benchmark.pedantic(run, rounds=rounds, iterations=iterations)

    return bench_init


def _contains(cases: list, rounds: int, iterations: int):
    @pytest.mark.parametrize("hit_density", HIT_DENSITIES)
    @pytest.mark.parametrize("case", cases)
    def bench_contains(benchmark, case: BenchmarkCase, hit_density: float):
        optimized = instance_from_case(case)
        buffer = list(range(int(len(optimized) / hit_density)))
        random.shuffle(buffer)
        values = itertools.cycle(buffer)

        def run():
            next(values) in optimized

        benchmark.pedantic(run, rounds=rounds, iterations=iterations)

    return bench_contains


def _iter(cases: list, rounds: int, iterations: int):
    @pytest.mark.parametrize("case", cases)
    def bench_iter(benchmark, case: BenchmarkCase):
        optimized = instance_from_case(case)

        def run():
            [el for el in optimized]

        benchmark.pedantic(run, rounds=rounds, iterations=iterations)

    return bench_iter


def _len(cases: list, rounds: int, iterations: int):
    @pytest.mark.parametrize("case", cases)
    def bench_len(benchmark, case: BenchmarkCase):
        optimized = instance_from_case(case)

        def run():
            len(optimized)

        benchmark.pedantic(run, rounds=rounds, iterations=iterations)

    return bench_len


init = BenchmarkOperation(name="bench_init", fn=_init)
contains = BenchmarkOperation(name="bench_contains", fn=_contains)
iter_ = BenchmarkOperation(name="bench_iter", fn=_iter)
len_ = BenchmarkOperation(name="bench_len", fn=_len)
