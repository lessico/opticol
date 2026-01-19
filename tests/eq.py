from collections.abc import Iterator, Sequence
from typing import Any


def seq(seq1: Sequence, seq2: Sequence) -> bool:
    """
    Return if two sequences are identical at the Sequence interface level.

    Note that the parameterized types of the Sequences do not matter for this check.

    Args:
        seq1: One of the sequences to compare for equality.
        seq2: The other sequence to compare for equality.

    Returns:
        True if the two sequences are identical and False otherwise.
    """
    if len(seq1) != len(seq2):
        return False

    for item1, item2 in zip(seq1, seq2):
        if item1 != item2:
            return False

    return True


def seq_op_result(first: Any, second: Any, materialized_cache: dict[Iterator, list]) -> bool:
    """
    Checks if the result of two Sequence operations are identical.

    The results are obtained if the Sequence operation succeeds and does not raise an error.
    Sequence operation here refers to those operations defined on the ABC collection documentation
    as required to implement, and mixins.

    Based on this documentation, the only possible results from a Sequence operation are an
    Iterator, another Sequence, an item from the Sequence or a boolean.

    Args:
        first: The first result to compare.
        second: The second result to compare.
        materialized_cache: The per harness cache of iterators their in-memory materialized version.

    Returns:
        True if the results of the operation are identical, and False otherwise.
    """
    if isinstance(first, Iterator) and isinstance(second, Iterator):
        if first not in materialized_cache:
            materialized_cache[first] = list(first)
        f = materialized_cache[first]

        if second not in materialized_cache:
            materialized_cache[second] = list(second)
        s = materialized_cache[second]

        return seq(f, s)
    elif isinstance(first, Sequence) and isinstance(second, Sequence):
        return seq(first, second)

    # The results of the operations are either elements from the sequence or a boolean.
    return first == second
