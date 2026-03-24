"""Shared benchmark operation descriptors for Mapping and MutableMapping benchmarks."""

from collections.abc import Callable, Mapping, MutableMapping
import itertools

from benchmarks.common import (
    BenchmarkCase,
    BenchmarkOperation,
    instance_from_case,
    proportional_indexer,
    HIT_DENSITIES,
)


def _init(case: BenchmarkCase[Mapping]) -> Callable[[], None]:
    cls = case.cls
    seed = case.seed()

    def run():
        cls(seed)

    return run


def _getitem(case: BenchmarkCase[Mapping], hit_density: float) -> Callable[[], None]:
    optimized = instance_from_case(case)
    keys = proportional_indexer(optimized, hit_density)

    def run():
        try:
            optimized[next(keys)]
        except KeyError:
            pass

    return run


def _iter(case: BenchmarkCase[Mapping]) -> Callable[[], None]:
    optimized = instance_from_case(case)

    def run():
        for _ in optimized:
            pass

    return run


def _len(case: BenchmarkCase[Mapping]) -> Callable[[], None]:
    optimized = instance_from_case(case)

    def run():
        len(optimized)

    return run


def _setitem(case: BenchmarkCase[MutableMapping], hit_density: float) -> Callable[[], None]:
    s = case.seed()
    keys = proportional_indexer(s, hit_density)
    values = itertools.cycle(s.values())

    def run():
        instance = case.cls(s)
        instance[next(keys)] = next(values)

    return run


def _delitem(case: BenchmarkCase[MutableMapping], hit_density: float) -> Callable[[], None]:
    s = case.seed()
    keys = proportional_indexer(s, hit_density)

    def run():
        instance = case.cls(s)
        try:
            del instance[next(keys)]
        except KeyError:
            pass

    return run


init = BenchmarkOperation(key="init", fn=_init)
getitem = BenchmarkOperation(key="getitem", fn=_getitem).with_params(hit_density=HIT_DENSITIES)
iter_ = BenchmarkOperation(key="iter", fn=_iter)
len_ = BenchmarkOperation(key="len", fn=_len)
setitem = BenchmarkOperation(key="setitem", fn=_setitem).with_params(hit_density=HIT_DENSITIES)
delitem = BenchmarkOperation(key="delitem", fn=_delitem).with_params(hit_density=HIT_DENSITIES)
