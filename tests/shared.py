from collections.abc import Iterator, Sequence
from typing import Any, Callable


type Factory[C] = Callable[[C], C]


def _success_label(success: bool) -> str:
    """
    Convert a flag indicating success into a past participle for error message creation.

    Args:
        success: True if the thing being labeled was successful.

    Returns:
        'succeeded' if the flag is True and 'failed' otherwise.
    """
    if success:
        return "succeeded"

    return "failed"


def _assert_eq_op(
    unk: tuple[bool, Any],
    ref: tuple[bool, Any],
    unk_idx: int,
    op_idx: int,
    op_equality: Callable[[Any, Any, dict], bool],
    materialized_cache: dict[Iterator, list]
) -> None:
    """
    Assert that two operations on a Sequence have the same output.

    The operation if successful, has some output, but in the error case, will raise an error. So the
    first value is a flag if the operation was successful, and the second value is either the result
    of the operation or the error that was raised.

    Args:
        unk: The result that is being compared against a reference.
        ref: The reference being compared against.
        unk_idx: Used for crafing the assert message in the case of any failure. Indexes the unknown
            sequence instance.
        op_idx: The operation index operating on the different sequence instances.
        materialized_list: The per harness cache of iterators to lists.
    """
    assert unk[0] == ref[0], (
        f"The operation at index {op_idx} {_success_label(unk[0])} on the factory at index "
        f"{unk_idx} with result '{ref[1]}' while the first factory {_success_label(ref[0])} "
        f"with result {ref[1]}."
    )

    # If the operation did not raise any error, then just compare the results otherwise, the error
    # check just ensures that they are the same error types, since there is no other reliable and
    # deeper comparison available.
    if unk[0]:
        assert op_equality(unk[1], ref[1], materialized_cache)
    else:
        assert type(unk[1]) == type(ref[1])


def harness[C](
    seed: C,
    factories: Sequence[Factory[C]],
    ops: Sequence[Callable[[C], Any]],
    collection_equality: Callable[[C, C], bool],
    op_equality: Callable[[Any, Any, dict], bool]
) -> None:
    """
    The main test harness for Sequences and which can be used to establish API level equivalence.

    There are technically no behavior level definitions of Sequences and there are a lot of edge
    cases, so the easiest way to test behavior is to compare the effects and results of different
    implementations on various interface definitions.

    Args:
        seed: The value that is provided to the various factories to create the Sequence instances.
        factories: The implementations to test via the harness.
        ops: The operations to call on the Sequence. The results will be validated and any mutations
            to the underlying Sequence will be compared as well.
        collection_equality:
        op_equality:
    """
    if len(factories) < 2:
        raise ValueError("Expected at least two factories to compare operations on.")

    targets = [factory(seed) for factory in factories]

    def run(current, op):
        successful = True
        try:
            result = op(current)
        except Exception as exc:
            successful = False
            result = exc

        return (successful, result)

    for i, op in enumerate(ops):
        materialized_cache: dict[Iterator, list] = {}
        results = [run(target, op) for target in targets]

        for j, sub in enumerate(results[1:], 1):
            _assert_eq_op(sub, results[0], j, i, op_equality, materialized_cache)

        for target in targets[1:]:
            assert collection_equality(targets[0], target)

