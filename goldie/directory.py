import glob
import inspect
import os.path
import unittest
from dataclasses import dataclass

from goldie.compare import ConfigComparison, compare
from goldie.run import ConfigRun, ConfigRunValidation, run


@dataclass
class ConfigDirectoryTest:
    """Configuration for directory based golden file testing."""

    directory: str
    """The directory to search for test files."""
    file_filter: str
    """The file filter to use to find test files."""
    run_configuration: ConfigRun
    """The run configuration to use to run the command."""
    run_validation_configuration: ConfigRunValidation
    """The run validation configuration to use to validate the command."""
    comparison_configuration: ConfigComparison
    """The configuration for comparing the actual and golden files."""


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
    name, ext = os.path.splitext(path)
    name = os.path.basename(name)
    return f"{name}.golden{ext}"


def _get_caller_directory() -> str:
    """
    Get the directory of the caller.

    Returns
    -------
    str
        The directory of the caller.
    """
    # Get the current stack frame
    current_frame = inspect.currentframe()
    # Get the frame of the caller
    caller_frame = current_frame.f_back
    # Get the filename of the caller
    caller_filename = caller_frame.f_code.co_filename
    # Get the directory of the caller
    caller_directory = os.path.dirname(caller_filename)
    return caller_directory


def run_unittest(
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

    # Find all relevant files in the directory
    test_files = glob.glob(os.path.join(_get_caller_directory(), configuration.directory, configuration.file_filter))

    # Iterate over the test cases
    for i, (test_file) in enumerate(test_files):
        with test.subTest(file=test_file):
            # Get the golden file
            golden_file = _get_golden_filename(test_file)

            # Run the command
            exit_code, actual_file = run(test_file, configuration.run_configuration)

            # Assert the exit code
            if configuration.run_validation_configuration.validate_exit_code:
                test.assertEqual(
                    exit_code,
                    configuration.run_validation_configuration.expected_exit_code,
                    f"Expected exit code {configuration.run_validation_configuration.expected_exit_code}, but got {exit_code}.",
                )

            # Update the golden file if necessary
            if os.environ.get("GOLDIE_UPDATE", "false").lower() == "true":
                with open(golden_file, "w") as f:
                    f.write(open(actual_file, "r").read())
                continue

            # Compare the actual and golden files
            equal, message, differences = compare(actual_file, golden_file, configuration.comparison_configuration)
            # Prepare the message
            if differences:
                message += "\n" + "\n".join(
                    [f"{d.location}: {d.message} ({d.expected} != {d.actual})" for d in differences]
                )
            # Assert the comparison
            test.assertTrue(equal, message)
