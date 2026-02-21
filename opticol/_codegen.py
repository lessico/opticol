"""
Internal module to consolidate dynamic code generation logic and modifications.
"""

from collections.abc import Iterable


def guard(flag: bool, code: str) -> str:
    if flag:
        return code
    return ""


def spliced(level: int, lines: Iterable[str]) -> str:
    sep = "\n" + ("    " * level)
    return sep.join(lines)


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
