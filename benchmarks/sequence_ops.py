"""Shared benchmark operation descriptors for Sequence and MutableSequence benchmarks."""

from collections.abc import Callable, MutableSequence, Sequence
import itertools

from benchmarks.common import BenchmarkCase, BenchmarkOperation, instance_from_case


def _init(case: BenchmarkCase[Sequence]) -> Callable[[], None]:
    cls = case.cls
    seed = case.seed()

    def run():
        cls(seed)

    return run


def _getitem(case: BenchmarkCase[Sequence]) -> Callable[[], None]:
    optimized = instance_from_case(case)
    indices = itertools.cycle(range(len(optimized)))

    def run():
        optimized[next(indices)]

    return run


def _len(case: BenchmarkCase[Sequence]) -> Callable[[], None]:
    optimized = instance_from_case(case)

    def run():
        len(optimized)

    return run


def _setitem(case: BenchmarkCase[MutableSequence]) -> Callable[[], None]:
    s = case.seed()
    internal_size = len(s)
    indices = itertools.cycle(range(internal_size))
    values = itertools.cycle(range(internal_size))

    def run():
        instance = case.cls(s)
        instance[next(indices)] = next(values)

    return run


def _delitem(case: BenchmarkCase[MutableSequence]) -> Callable[[], None]:
    s = case.seed()
    internal_size = len(s)
    indices = itertools.cycle(range(internal_size))

    def run():
        instance = case.cls(s)
        del instance[next(indices)]

    return run


def _insert(case: BenchmarkCase[MutableSequence]) -> Callable[[], None]:
    s = case.seed()
    internal_size = len(s)
    indices = itertools.cycle(range(internal_size))
    values = itertools.cycle(range(internal_size))

    def run():
        instance = case.cls(s)
        instance.insert(next(indices), next(values))

    return run


init = BenchmarkOperation(key="init", fn=_init)
getitem = BenchmarkOperation(key="getitem", fn=_getitem)
len_ = BenchmarkOperation(key="len", fn=_len)
setitem = BenchmarkOperation(key="setitem", fn=_setitem)
delitem = BenchmarkOperation(key="delitem", fn=_delitem)
insert = BenchmarkOperation(key="insert", fn=_insert)
