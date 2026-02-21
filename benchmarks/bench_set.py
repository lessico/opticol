import random
import pytest
from opticol.factory import create_set_class

MAX_FIXTURE_SIZE = 10

basic_int_sets = [set(range(i)) for i in range(1, MAX_FIXTURE_SIZE)]

@pytest.mark.parametrize("fixture", basic_int_sets)
def test_bench_init(benchmark, fixture):
    l = len(fixture)
    c = create_set_class(l)

    def run():
        c(fixture)

    benchmark(run)

@pytest.mark.parametrize("fixture", basic_int_sets)
def test_bench_contains(benchmark, fixture):
    l = len(fixture)
    c = create_set_class(l)
    optimized = c(fixture)

    i = random.randint(0, MAX_FIXTURE_SIZE - 1)

    def run():
        i % l in optimized

    benchmark(run)

@pytest.mark.parametrize("fixture", basic_int_sets)
def test_bench_iter(benchmark, fixture):
    l = len(fixture)
    c = create_set_class(l)
    optimized = c(fixture)

    def run():
        [el for el in optimized]

    benchmark(run)

@pytest.mark.parametrize("fixture", basic_int_sets)
def test_bench_len(benchmark, fixture):
    l = len(fixture)
    c = create_set_class(l)
    optimized = c(fixture)

    def run():
        len(optimized)

    benchmark(run)