import glob
import inspect
import os.path
import unittest
from dataclasses import dataclass


@dataclass
class Configuration:
    """Configuration for directory based golden file testing."""

    directory: str
    file_filter: str


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
    configuration: Configuration,
):
    """
    Run the golden file test.

    Parameters
    ----------
    test : unittest.TestCase
        The test case to run.
    configuration : Configuration
        The configuration for the golden file test.
    """

    # Find all relevant files in the directory
    test_files = glob.glob(os.path.join(_get_caller_directory(), configuration.directory, configuration.file_filter))

    # Iterate over the test cases
    for i, (test_file) in enumerate(test_files):
        with test.subTest(file=test_file):
            # Get the golden file
            golden_file = _get_golden_filename(test_file)

            # Read the test file

            # Assert the content
            test.assertEqual(actual, expected, f"Test case {i} failed.")
