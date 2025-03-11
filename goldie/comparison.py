import json
import re
from dataclasses import dataclass, field
from enum import Enum

from jflat import flatten, unflatten

from .diff import Difference, DiffStyle, diff_color_code_full, diff_color_code_unified


class ComparisonType(Enum):
    """The type of comparison."""

    STRING = "string"
    """Comparison based on strings."""
    JSON = "json"
    """Comparison based on JSON."""
    BINARY = "binary"
    """Comparison based on binary files."""


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
class ConfigProcessJson:
    """Configuration for comparing dictionaries based on JSON."""

    replacements: list[JsonReplacement] = field(default_factory=list)
    """List of paths to replace."""
    roundings: list[JsonRounding] = field(default_factory=list)
    """List of paths to round before comparing."""
    precision: int = 6
    """The precision to round to."""


@dataclass
class ConfigCompareJson:
    """Configuration for comparing dictionaries based on JSON."""

    ignores: list[str] = field(default_factory=list)
    """List of paths to ignore."""
    allow_additional_keys: bool = False
    """Whether additional keys in the actual JSON are allowed."""
    allow_missing_keys: bool = False
    """Whether missing keys in the actual JSON are allowed."""


@dataclass
class ConfigProcessString:
    """Configuration for processing strings."""

    regex_replacements: list[RegexReplacement] = field(default_factory=list)
    """List of regex replacements."""


@dataclass
class ConfigCompareString:
    """Configuration for comparing strings."""

    diff_style: DiffStyle = DiffStyle.FULL
    """The diff style to use."""


@dataclass
class ConfigComparison:
    """Configuration for comparing actual and expected."""

    comparison_type: ComparisonType = ComparisonType.STRING
    """The type of comparison."""

    string_processing_config: ConfigProcessString = None
    """The configuration for processing strings."""
    string_comparison_config: ConfigCompareString = field(default_factory=ConfigCompareString)
    """The configuration for comparing strings."""
    json_processing_config: ConfigProcessJson = None
    """The configuration for processing JSON."""
    json_comparison_config: ConfigCompareJson = field(default_factory=ConfigCompareJson)
    """The configuration for comparing JSON."""


def _parse_json(json_str: str, decoder: any = None) -> tuple[dict, bool, str]:
    """
    Parse a JSON string.

    Parameters
    ----------
    json_str : str
        The JSON string.
    decoder : any
        The decoder to use.

    Returns
    -------
    tuple[dict, bool, str]
        The parsed JSON, a boolean indicating if the parsing was successful, and an error message.
    """

    try:
        if decoder:
            return decoder(json_str), True, ""
        return json.loads(json_str), True, ""
    except json.JSONDecodeError as e:
        return {}, False, str(e)


def process_string(
    actual: str,
    configuration: ConfigProcessString,
) -> str:
    """
    Processes a string according to the processing configuration.

    Parameters
    ----------
    actual : str
        The actual string.
    configuration : ConfigProcessString
        The processing configuration.

    Returns
    -------
    str
        The processed string.
    """

    # Apply regex replacements
    for replacement in configuration.regex_replacements:
        actual = re.sub(replacement.pattern, replacement.replacement, actual)

    return actual


def compare_string(
    actual: str,
    expected: str,
    configuration: ConfigCompareString,
) -> tuple[bool, str]:
    """
    Compares two strings according to the comparison configuration."

    Parameters
    ----------
    actual : str
        The actual string.
    expected : str
        The expected string.
    configuration : ConfigCompareString
        The comparison configuration.

    Returns
    -------
    tuple[bool, str]
        A tuple with a boolean indicating if the strings are equal and the diff.
    """

    if configuration.diff_style == DiffStyle.FULL:
        return actual == expected, diff_color_code_full(actual, expected)
    return actual == expected, diff_color_code_unified(actual, expected)


def process_json(
    actual: dict,
    configuration: ConfigProcessJson,
) -> dict:
    """
    Processes a dictionary according to the processing configuration.

    Parameters
    ----------
    actual : dict
        The actual dictionary.
    configuration : ConfigProcessJson
        The processing configuration.

    Returns
    -------
    dict
        The processed dictionary.
    """

    # Flatten the dictionaries
    actual_flat = flatten(actual)

    # Apply replacements
    for replacement in configuration.replacements:
        actual_flat[replacement.path] = replacement.value

    # Apply explicit roundings
    for rounding in configuration.roundings:
        if not isinstance(actual_flat[rounding.path], float):
            return (
                False,
                f"Expected number at rounding path '{rounding.path}' "
                + f"but got '{type(actual_flat[rounding.path])}' (actual: {actual_flat[rounding.path]})",
            )
        actual_flat[rounding.path] = round(actual_flat[rounding.path], rounding.precision)

    # Apply rounding to all numbers
    for path, value in actual_flat.items():
        if isinstance(value, float):
            actual_flat[path] = round(value, configuration.precision)

    # Unflatten and return
    return unflatten(actual_flat)


def compare_json(
    actual: dict,
    expected: dict,
    configuration: ConfigCompareJson,
) -> tuple[bool, list[Difference]]:
    """
    Compares two dictionaries according to the comparison configuration."

    Parameters
    ----------
    actual : dict
        The actual dictionary.
    expected : dict
        The expected dictionary.
    configuration : ConfigCompareJson
        The comparison configuration.

    Returns
    -------
    tuple[bool, list[Difference]]
        A tuple with a boolean indicating if the dictionaries are equal and a list of differences.
    """

    # Flatten the dictionaries
    actual_flat = flatten(actual)
    expected_flat = flatten(expected)

    # Collect all differences
    differences = []
    for path in set(actual_flat.keys()) | set(expected_flat.keys()):
        if path in configuration.ignores:
            continue
        if path not in actual_flat and not configuration.allow_missing_keys:
            # MISSING KEY
            differences.append(
                Difference(
                    expected=expected_flat[path],
                    actual="",
                    location=path,
                    message="Missing key.",
                )
            )
        elif path not in expected_flat and not configuration.allow_additional_keys:
            # ADDITIONAL KEY
            differences.append(
                Difference(
                    expected="",
                    actual=actual_flat[path],
                    location=path,
                    message="Additional key.",
                )
            )
        elif type(actual_flat[path]) is not type(expected_flat[path]):
            # TYPE
            differences.append(
                Difference(
                    expected=expected_flat[path],
                    actual=actual_flat[path],
                    location=path,
                    message="Difference in type. "
                    + f"Expected {type(expected_flat[path])}, but got {type(actual_flat[path])}.",
                )
            )
        elif actual_flat[path] != expected_flat[path]:
            # SIMPLE EQUALITY
            differences.append(
                Difference(
                    expected=expected_flat[path],
                    actual=actual_flat[path],
                    location=path,
                    message="Difference in value.",
                )
            )

    # Return the result
    return not differences, differences


def process(
    actual_file: str,
    configuration: ConfigComparison,
    json_decoder: any = None,
    json_encoder: any = None,
):
    """
    Processes a file in place according to the processing configuration."
    """

    # Handle binary processing
    if configuration.comparison_type == ComparisonType.BINARY:
        return

    # Read the file
    with open(actual_file, "r") as f:
        actual = f.read()

    # Process the actual string
    if configuration.string_processing_config:
        actual = process_string(actual, configuration.string_processing_config)
        if configuration.comparison_type == ComparisonType.STRING:
            with open(actual_file, "w") as f:
                f.write(actual)
            return

    # Decode the JSON
    actual_json, parse_ok, parse_error = _parse_json(actual, json_decoder)
    if not parse_ok:
        raise ValueError(f"Error parsing JSON: {parse_error}, content: {actual}")

    # Process the actual JSON
    if configuration.json_processing_config:
        actual_json = process_json(actual_json, configuration.json_processing_config)

    # Write the processed JSON
    with open(actual_file, "w") as f:
        if json_encoder:
            f.write(json_encoder(actual_json))
        else:
            json.dump(actual_json, f, indent=4)


def compare(
    actual_file: str,
    golden_file: str,
    configuration: ConfigComparison,
    json_decoder: any = None,
) -> tuple[bool, str, list[Difference]]:
    """
    Compares two files according to the comparison configuration."
    """

    # Handle binary comparison
    if configuration.comparison_type == ComparisonType.BINARY:
        with open(actual_file, "rb") as f:
            actual = f.read()
        with open(golden_file, "rb") as f:
            expected = f.read()
        equal = actual == expected
        return equal, "Content is equal." if equal else "Content is not equal.", []

    # Read the files
    with open(actual_file, "r") as f:
        actual = f.read()
    with open(golden_file, "r") as f:
        expected = f.read()

    # Process the actual string
    if configuration.string_processing_config:
        actual = process_string(actual, configuration.string_processing_config)

    # Handle string comparison
    if configuration.comparison_type == ComparisonType.STRING:
        equal, diff = compare_string(actual, expected, configuration.string_comparison_config)
        return equal, diff, []

    # Decode the JSON
    if json_decoder:
        actual = json_decoder(actual)
        expected = json_decoder(expected)
    else:
        actual = json.loads(actual)
        expected = json.loads(expected)

    # Process the actual JSON
    if configuration.json_processing_config:
        actual = process_json(actual, configuration.json_processing_config)

    # Handle JSON comparison
    equal, differences = compare_json(actual, expected, configuration.json_comparison_config)
    return equal, "Content is equal." if equal else "Content is not equal.", differences
