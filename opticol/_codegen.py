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
    if flag:
        return code
    return other


def spliced(level: int, strs: Sequence[str]) -> str:
    sep = "\n" + ("    " * level)
    ls = [l for s in strs for l in rootit(s).splitlines()]
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
