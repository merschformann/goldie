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
class ConfigDirectoryTest:
    """Configuration for directory based golden file testing."""

    file_filter: str
    """The file filter to use to find test files."""
    comparison_configuration: ConfigComparison
    """The configuration for comparing the actual and golden files."""
    run_configuration: ConfigRun
    """The run configuration to use to run the command."""
    run_validation_configuration: ConfigRunValidation = field(default_factory=lambda: ConfigRunValidation())
    """The run validation configuration to use to validate the command."""


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


def _get_caller_directory() -> str:
    """
    Get the directory of the caller's caller.

    Returns
    -------
    str
        The directory.
    """
    abs_path = os.path.abspath((inspect.stack()[2])[1])
    directory_of_1py = os.path.dirname(abs_path)
    return directory_of_1py


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
    root_directory = _get_caller_directory()
    test_files = glob.glob(os.path.join(root_directory, configuration.file_filter))

    # Remove any golden files
    test_files = [f for f in test_files if not f.endswith(".golden")]

    # Iterate over the test cases
    for i, (input_file) in enumerate(test_files):
        with test.subTest(file=input_file), tempfile.NamedTemporaryFile("w+") as output_file:
            # Get the golden file
            golden_file = _get_golden_filename(input_file)

            # Run the command
            exit_code = execute(input_file, output_file.name, root_directory, configuration.run_configuration)

            # Assert the exit code
            if configuration.run_validation_configuration.validate_exit_code:
                test.assertEqual(
                    exit_code,
                    configuration.run_validation_configuration.expected_exit_code,
                    f"Expected exit code {configuration.run_validation_configuration.expected_exit_code}, but got {exit_code}.",
                )

            # Process the file
            process(output_file.name, configuration.comparison_configuration)

            # Update the golden file if necessary
            if UPDATE:
                with open(golden_file, "w") as f:
                    f.write(json.dumps(json.load(output_file), indent=4))
                continue

            # Compare the actual and golden files
            equal, message, differences = compare(output_file.name, golden_file, configuration.comparison_configuration)
            # Prepare the message
            if differences:
                message += "\n" + "\n".join(
                    [f"{d.location}: {d.message} ({d.expected} != {d.actual})" for d in differences]
                )
            # Assert the comparison
            test.assertTrue(equal, message)
