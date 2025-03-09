import re
from dataclasses import dataclass, field

from jpathflat import flatten

from .diff import DiffStyle, diff_color_code_full, diff_color_code_unified


@dataclass
class RegexReplacement:
    """Defines a regex replacement."""

    pattern: str
    """The pattern to be replaced in Python 're' regex format."""
    replacement: str
    """The replacement string."""


@dataclass
class JsonReplacement:
    """Defines a JSON replacement."""

    path: str
    """The JSON path to be replaced."""
    value: any
    """The value to put in place of the path."""


@dataclass
class JsonRounding:
    """Defines rounding for a specific JSON path."""

    path: str
    """The JSON path to be rounded before comparing."""
    precision: int
    """The precision to round to."""


@dataclass
class ComparisonConfigurationJson:
    """Configuration for comparing dictionaries based on JSON."""

    ignores: list[str] = field(default_factory=list)
    """List of paths to ignore."""
    replacements: list[JsonReplacement] = field(default_factory=list)
    """List of paths to replace."""
    roundings: list[JsonRounding] = field(default_factory=list)
    """List of paths to round before comparing."""
    precision: int = 6
    """The precision to round to."""
    allow_additional_keys: bool = False
    """Whether additional keys in the actual JSON are allowed."""
    allow_missing_keys: bool = False
    """Whether missing keys in the actual JSON are allowed."""


@dataclass
class ComparisonConfigurationString:
    """Configuration for comparing strings."""

    regex_replacements: list[RegexReplacement] = field(default_factory=list)
    """List of regex replacements."""
    diff_style: DiffStyle = DiffStyle.FULL
    """The diff style to use."""


@dataclass
class ComparisonConfiguration:
    """Configuration for comparing strings."""

    string_comparison_config: ComparisonConfigurationString
    """The configuration for comparing strings."""
    json_comparison_config: ComparisonConfigurationJson = None
    """
    The configuration for comparing JSON objects.
    If present, the comparison will be done using the JSON structure and configuration.
    Otherwise, it will fall back to the string comparison (and its configuration).
    """


def compare(
    actual: str,
    expected: str,
    configuration: ComparisonConfiguration,
    json_decoder: any = None,
) -> tuple[bool, str]:
    """
    Compares two strings according to the comparison configuration."

    Parameters
    ----------
    actual : str
        The actual string.
    expected : str
        The expected string.
    configuration : ComparisonConfiguration
        The comparison configuration.

    Returns
    -------
    tuple[bool, str]
        A tuple with a boolean indicating if the strings are equal and a message.
    """

    # Apply regex replacements
    for replacement in configuration.regex_replacements:
        actual = re.sub(replacement.pattern, replacement.replacement, actual)

    # If JSON configuration is not present, fall back to string comparison
    if configuration.json_comparison_config is None:
        if configuration.string_comparison_config.diff_style == DiffStyle.FULL:
            return actual == expected, diff_color_code_full(actual, expected)
        return actual == expected, diff_color_code_unified(actual, expected)

    # Decode JSON
    actual_json = json_decoder(actual)
    expected_json = json_decoder(expected)

    # Compare JSON
    return _compare_json(actual_json, expected_json, configuration.json_comparison_config)


def _compare_json(
    actual: dict,
    expected: dict,
    configuration: ComparisonConfigurationJson,
) -> tuple[bool, str]:
    """
    Compares two dictionaries according to the comparison configuration."

    Parameters
    ----------
    actual : dict
        The actual dictionary.
    expected : dict
        The expected dictionary.
    configuration : ComparisonConfigurationJson
        The comparison configuration.

    Returns
    -------
    tuple[bool, str]
        A tuple with a boolean indicating if the dictionaries are equal and a message.
    """

    # Flatten the dictionaries
    actual_flat = flatten(actual)
    expected_flat = flatten(expected)

    # Apply replacements
    for replacement in configuration.replacements:
        actual_flat[replacement.path] = replacement.value
        expected_flat[replacement.path] = replacement.value

    # Apply roundings
    for rounding in configuration.roundings:
        if not isinstance(actual_flat[rounding.path], (int, float)):
            return (
                False,
                f"Expected number at rounding path '{rounding.path}' "
                + f"but got '{type(actual_flat[rounding.path])}' (actual: {actual_flat[rounding.path]})",
            )
        actual_flat[rounding.path] = round(actual_flat[rounding.path], rounding.precision)
        expected_flat[rounding.path] = round(expected_flat[rounding.path], rounding.precision)

    # Collect all differences
    differences = []
    for path in set(actual_flat.keys()) | set(expected_flat.keys()):
        if path in configuration.ignores:
            continue
        if path not in actual_flat and not configuration.allow_missing_keys:
            differences.append(f"Expected '{path}' but got nothing.")
        elif path not in expected_flat and not configuration.allow_additional_keys:
            differences.append(f"Expected nothing but got '{path}'.")
        elif actual_flat[path] != expected_flat[path]:
            differences.append(f"Expected '{path}' to be '{expected_flat[path]}' but got '{actual_flat[path]}'.")

    # Return the result
    if differences:
        return False, "\n".join(differences)
    return True, "No differences found."
