import os
import re
import unittest

import goldie.diff


def _file_path(relative_path: str) -> str:
    """
    Returns the full path to a file relative to the testdata directory.

    Parameters
    ----------
    relative_location : str
        The relative location of the file (e.g.: just the file name).

    Returns
    -------
    str
        The full path to the file.
    """

    return os.path.join(os.path.dirname(__file__), "testdata", relative_path)


class TestDiff(unittest.TestCase):
    def test_diff(self):
        with open(_file_path("comparison-1.txt")) as f:
            comparison_1 = f.read()
        with open(_file_path("comparison-2.txt")) as f:
            comparison_2 = f.read()

        diff = goldie.diff.diff_color_code_full(comparison_1, comparison_2)

        clean_diff = re.sub(r"\x1b\[[\d\;]+m", "", diff)
        self.assertIn("moosunlight", clean_diff)
        self.assertEqual(len(diff.split("\n")), 11)
