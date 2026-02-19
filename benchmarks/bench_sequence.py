import random
import pytest
from opticol.factory import create_seq_class, create_mut_seq_class

MAX_FIXTURE_SIZE = 10

basic_int_lists = [list(range(i)) for i in range(1, MAX_FIXTURE_SIZE)]

@pytest.mark.parametrize("fixture", basic_int_lists)
def test_bench_get_random_item(benchmark, fixture):
    l = len(fixture)
    c = create_seq_class(l)
    optimized = c(fixture)

    i = random.randint(0, MAX_FIXTURE_SIZE - 1)

    def run():
        optimized[i % l]

    benchmark(run)

@pytest.mark.parametrize("fixture", basic_int_lists)
def test_bench_set_random_item(benchmark, fixture):
    l = len(fixture)
    c = create_mut_seq_class(l)
    optimized = c(fixture)

    i = random.randint(0, MAX_FIXTURE_SIZE - 1)

    def run():
        optimized[i % l] = i

    benchmark(run)
