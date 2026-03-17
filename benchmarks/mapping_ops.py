"""Shared benchmark operation descriptors for Mapping and MutableMapping benchmarks."""

from collections.abc import Callable, Mapping, MutableMapping
import itertools

from benchmarks.common import BenchmarkCase, BenchmarkOperation, instance_from_case


def _init(case: BenchmarkCase[Mapping]) -> Callable[[], None]:
    cls = case.cls
    seed = case.seed()

    def run():
        cls(seed)

    return run


def _getitem(case: BenchmarkCase[Mapping]) -> Callable[[], None]:
    optimized = instance_from_case(case)
    keys = itertools.cycle(optimized)

    def run():
        optimized[next(keys)]

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


def _setitem(case: BenchmarkCase[MutableMapping]) -> Callable[[], None]:
    s = case.seed()
    keys = itertools.cycle(s)
    values = itertools.cycle(s.values())

    def run():
        instance = case.cls(s)
        instance[next(keys)] = next(values)

    return run


def _delitem(case: BenchmarkCase[MutableMapping]) -> Callable[[], None]:
    s = case.seed()
    keys = itertools.cycle(s)

    def run():
        instance = case.cls(s)
        del instance[next(keys)]

    return run


init = BenchmarkOperation(key="init", fn=_init)
getitem = BenchmarkOperation(key="getitem", fn=_getitem)
iter_ = BenchmarkOperation(key="iter", fn=_iter)
len_ = BenchmarkOperation(key="len", fn=_len)
setitem = BenchmarkOperation(key="setitem", fn=_setitem)
delitem = BenchmarkOperation(key="delitem", fn=_delitem)
