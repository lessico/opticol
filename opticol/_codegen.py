"""
Internal module to consolidate dynamic code generation logic and modifications.
"""

from collections.abc import Sequence
from typing import Any


def def_fn(code: str, **kwargs) -> Any:
    """
    Easily define a function dynamically using a string at runtime.

    The code string that is given is passed through rootit so that it is automatically rooted and
    does not have to be at the root identation level on the call itself.

    Args:
        code: The code that defines the function and will be dynamically executed.
        kwargs: The items to add to the namespace the function will be defined in.

    Returns:
        The object that was added to the dynamic namespace by the code string.

    Raises:
        A runtime error if not exactly 1 object was added to this namespace.
    """
    rooted = rootit(code)

    original_keys = set(kwargs.keys())
    ns: dict[str, Any] = kwargs
    exec(rooted, ns)
    current_keys = set(kwargs.keys())
    defined = current_keys - original_keys - {"__builtins__"}

    if len(defined) == 1:
        key = defined.pop()
        return ns[key]

    raise RuntimeError("The dynamic execution namespace had an unexpected value.")


def guard(flag: bool, code: str, other: str = "") -> str:
    """
    Based on the result of the flag, will return one piece of code or another.

    Args:
        flag: The condition to determine which code to return.
        code: The code to return if the flag is True.
        other: The code to return if the flag is False. Defaults to empty string.

    Returns:
        The final evaluated code snippet based on the flag value.
    """
    if flag:
        return code
    return other


def splice(level: int, strs: Sequence[str]) -> str:
    """
    Splices the given code snippets with the given indentation level.

    The indentation level is added to the rooted versions of the strings, so this can help
    readability when splicing a multiline code snippet.

    Args:
        level: The desired indentation level to add to the code snippets.
        strs: The multiple code snippets to add the indentation level to and combine.

    Returns:
        The final composed, spliced together code snippet which joined all the strs with the desired
        indentation level.
    """
    sep = "\n" + ("    " * level)
    ls = [l for s in strs for l in rootit(s).splitlines()]
    return sep.join(ls)


def multisplice(level: int, seqs: Sequence[Sequence[str]]) -> str:
    """
    Nearly equivalent to splice but expects lines to be separated rather than provided as snippets,
    and does not root the provided strings.

    Args:
        level: The desired identation level to add to each line.
        seqs: The code snippets to splice together already split by line.

    Returns:
        The final composed string with identation levels added to each individual line as they were
        provided.
    """
    sep = "\n" + ("    " * level)
    ls = [line for seq in seqs for line in seq]
    return sep.join(ls)


def rootit(code: str) -> str:
    """
    Transform the indentation levels of the given Python code to be rooted.

    This is mostly a helper method to allow for easier inline dynamic code creation without
    requiring these strings to have indentation out of sync with the code it is defined with.

    Args:
        code: The code to transform.

    Returns:
        The rooted code with no base indentation.
    """
    lines = code.split("\n")
    if not lines:
        return code

    for first, line in enumerate(lines):
        if line:
            break
    else:
        return code

    prefix_chars = []
    for ch in lines[first]:
        if ch not in " \t":
            break
        if ch != lines[first][0]:
            raise RuntimeError("Inconsistent whitespace usage in IR being reformatted.")

        prefix_chars.append(ch)
    prefix = "".join(prefix_chars)

    new_lines = [lines[first].removeprefix(prefix)]
    for line in lines[first + 1 :]:
        if not line:
            continue
        if not line.startswith(prefix):
            raise RuntimeError("Expected whitespace prefix not found on one of the IR lines.")

        new_lines.append(line.removeprefix(prefix))

    return "\n".join(new_lines)
