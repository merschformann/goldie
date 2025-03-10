import difflib
from dataclasses import dataclass
from enum import Enum


@dataclass
class Difference:
    """
    Represents a difference between expectation and actual.
    """

    expected: any
    """The expected value."""
    actual: any
    """The actual value."""
    location: str = None
    """The location of the difference, if applicable."""
    message: str = None
    """The message of the difference, if applicable."""


class DiffStyle(Enum):
    FULL = "full"
    UNIFIED = "unified"


def _red(text):
    return f"\x1b[38;2;255;0;0m{text}\x1b[38;2;255;255;255m"


def _green(text):
    return f"\x1b[38;2;0;255;0m{text}\x1b[38;2;255;255;255m"


def _blue(text):
    return f"\x1b[38;2;0;0;255m{text}\x1b[38;2;255;255;255m"


def _cyan(text):
    return f"\x1b[38;2;0;255;255m{text}\x1b[38;2;255;255;255m"


def _white(text):
    return f"\x1b[38;2;255;255;255m{text}\x1b[38;2;255;255;255m"


def diff_color_code_full(old: str, new: str) -> str:
    """
    Returns a colored diff between two strings.

    Parameters
    ----------
    old : str
        The old string.
    new : str
        The new string.

    Returns
    -------
    str
        The colored diff.
    """
    result = ""
    codes = difflib.SequenceMatcher(a=old, b=new).get_opcodes()
    for code in codes:
        if code[0] == "equal":
            result += _white(new[code[3] : code[4]])
        elif code[0] == "delete":
            result += _red(old[code[1] : code[2]])
        elif code[0] == "insert":
            result += _green(new[code[3] : code[4]])
        elif code[0] == "replace":
            result += _red(old[code[1] : code[2]]) + _green(new[code[3] : code[4]])
    return result


def diff_color_code_unified(old: str, new: str, n: int = 3, line_sep: str = "\n") -> str:
    """
    Returns a colored diff between two strings based on lines.

    Parameters
    ----------
    old : str
        The old string.
    new : str
        The new string.
    n : int, optional
        The number of lines to show around the change, by default 3.
    line_sep : str, optional
        The line separator, by default "\n".

    Returns
    -------
    str
        The colored diff.
    """
    # Split the strings into lines using the provided line separator
    old_lines = old.split(line_sep)
    new_lines = new.split(line_sep)

    # Use difflib to compare lines instead of characters
    diff = difflib.unified_diff(old_lines, new_lines, n=n, lineterm="")
    result = []

    for line in diff:
        if line.startswith("+"):
            # New line (green)
            result.append(_green(line))
        elif line.startswith("-"):
            # Removed line (red)
            result.append(_red(line))
        elif line.startswith("@@"):
            # Hunk header (cyan or some other highlighting)
            result.append(_cyan(line))
        else:
            # Context line or other lines (white)
            result.append(_white(line))

    # Join all lines with the provided line separator
    return line_sep.join(result)
