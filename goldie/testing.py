import glob
import inspect
import json
import os.path
import tempfile
import unittest
from dataclasses import dataclass, field

from goldie.comparison import ConfigComparison, compare, process
from goldie.execution import ConfigRun, ConfigRunValidation, execute
from goldie.update import UPDATE


@dataclass
class TestDefinition:
    """A test definition for a golden file test."""

    input_file: str
    """The input file to use for the test."""
    extra_args: list[tuple[str, str]] = field(default_factory=list)
    """
    Extra arguments to pass to the command.
    These are given as a list of tuples with the placeholder and the value.
    """


@dataclass
class ConfigFileTest:
    """Configuration for file based golden file testing."""

    comparison_configuration: ConfigComparison
    """The configuration for comparing the actual and golden files."""
    run_configuration: ConfigRun
    """The run configuration to use to run the command."""
    run_validation_configuration: ConfigRunValidation = field(default_factory=lambda: ConfigRunValidation())


@dataclass
class ConfigDirectoryTest:
    """Configuration for directory based golden file testing."""

    config_file_test: ConfigFileTest
    """The common configuration applied to all tests."""
    file_filter: str = None
    """The file filter to use to find test files."""
    explicit_tests: list[TestDefinition] = field(default_factory=list)
    """A list of explicit files to test."""


def _get_golden_filename(path: str) -> str:
    """
    Get the golden filename from a path.

    Parameters
    ----------
    path : str
        The path to get the golden filename from.

    Returns
    -------
    str
        The golden filename.
    """
    return path + ".golden"


def _get_caller_directory():
    """
    Get the directory of the caller (first caller not in the same file).
    """
    # Get the current call stack
    stack = inspect.stack()

    # Get the file of the current function
    current_file = stack[0].filename

    # Iterate through the stack to find the first caller not in the same file
    for frame in stack[1:]:
        if frame.filename != current_file:
            return os.path.dirname(frame.filename)

    # If no such caller is found, return None or raise an exception
    raise ValueError("Unable to determine the caller directory.")


def run_file_unittest(
    test: unittest.TestCase,
    td: TestDefinition,
    configuration: ConfigFileTest,
):
    """
    Run the golden file test.

    Parameters
    ----------
    test : unittest.TestCase
        The test case to run.
    input_file : str
        The input file to use for the test.
    configuration : ConfigFileTest
        The configuration for the golden file test.
    """

    # Determine the root directory
    root_directory = _get_caller_directory()

    with tempfile.NamedTemporaryFile("w+") as output_file:
        # Get the golden file
        golden_file = _get_golden_filename(td.input_file)

        # Run the command
        exit_code = execute(
            input_file=td.input_file,
            output_file=output_file.name,
            cwd=root_directory,
            configuration=configuration.run_configuration,
            extra_args=td.extra_args,
        )

        # Assert the exit code
        if configuration.run_validation_configuration.validate_exit_code:
            test.assertEqual(
                exit_code,
                configuration.run_validation_configuration.expected_exit_code,
                f"Expected exit code {configuration.run_validation_configuration.expected_exit_code}"
                + f", but got {exit_code}.",
            )

        # Process the file
        process(output_file.name, configuration.comparison_configuration)

        # Update the golden file if necessary
        if UPDATE:
            with open(golden_file, "w") as f:
                f.write(json.dumps(json.load(output_file), indent=4))
            return

        # Compare the actual and golden files
        equal, message, differences = compare(output_file.name, golden_file, configuration.comparison_configuration)
        # Prepare the message
        if differences:
            message += "\n" + "\n".join(
                [f"{d.location}: {d.message} ({d.expected} != {d.actual})" for d in differences]
            )
        # Assert the comparison
        test.assertTrue(equal, message)


def run_directory_unittest(
    test: unittest.TestCase,
    configuration: ConfigDirectoryTest,
):
    """
    Run the golden file test.

    Parameters
    ----------
    test : unittest.TestCase
        The test case to run.
    configuration : ConfigDirectoryTest
        The configuration for the golden file test.
    """

    # Determine the root directory
    root_directory = _get_caller_directory()

    # Find files from file filter
    filter_files = []
    if configuration.file_filter is not None:
        filter_files = glob.glob(os.path.join(root_directory, configuration.file_filter))
        # Remove any golden files
        filter_files = [f for f in filter_files if not f.endswith(".golden")]

    # Convert to test definitions
    test_files = [TestDefinition(input_file) for input_file in filter_files]
    test_files.extend(configuration.explicit_tests)

    # Iterate over the test cases
    for i, td in enumerate(test_files):
        with test.subTest(f"Test {i}"):
            run_file_unittest(test, td, configuration.config_file_test)
