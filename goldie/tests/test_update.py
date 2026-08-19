import json
import os
import tempfile
import unittest
from unittest import mock

import goldie.testing
from goldie.comparison import ComparisonType, ConfigComparison, ConfigProcessString
from goldie.execution import ConfigRun, InputMode, OutputMode
from goldie.testing import ConfigFileTest, TestDefinition, run_file_unittest


class TestUpdate(unittest.TestCase):
    """Regression tests for updating golden files via GOLDIE_UPDATE.

    Previously the update logic read from the temporary output file *handle* instead of
    from the file on disk. Since the command output is written by name, the handle was
    never positioned at the start, so the golden file ended up empty. For JSON, the golden
    file was even truncated before the (failing) read, wiping any existing content.
    """

    def _run_update(
        self,
        input_content: str,
        comparison_type: ComparisonType,
        golden_seed: str,
        string_processing_config: ConfigProcessString = None,
    ) -> str:
        with tempfile.TemporaryDirectory() as directory:
            input_file = os.path.join(directory, "input.txt")
            with open(input_file, "w") as f:
                f.write(input_content)

            # Seed the golden file to make sure it is actually overwritten (and not just
            # left untouched or truncated to empty).
            golden_file = input_file + ".golden"
            with open(golden_file, "w") as f:
                f.write(golden_seed)

            configuration = ConfigFileTest(
                run_configuration=ConfigRun(
                    # `cat` simply echoes stdin to stdout.
                    cmd="cat",
                    args=[],
                    cwd=directory,
                    input_mode=InputMode.STDIN,
                    output_mode=OutputMode.STDOUT,
                ),
                comparison_configuration=ConfigComparison(
                    comparison_type=comparison_type,
                    string_processing_config=string_processing_config,
                ),
            )

            with mock.patch.object(goldie.testing, "UPDATE", True):
                run_file_unittest(
                    test=self,
                    td=TestDefinition(input_file=input_file),
                    configuration=configuration,
                )

            with open(golden_file) as f:
                return f.read()

    def test_update_json_writes_output(self):
        written = self._run_update('{"b": 2, "a": 1}', ComparisonType.JSON, golden_seed="STALE")

        self.assertNotEqual(written, "", "golden file must not be empty after update")
        self.assertEqual({"a": 1, "b": 2}, json.loads(written))

    def test_update_string_writes_output(self):
        written = self._run_update(
            "hello world",
            ComparisonType.STRING,
            golden_seed="STALE",
            string_processing_config=ConfigProcessString(),
        )

        self.assertEqual("hello world", written)


if __name__ == "__main__":
    unittest.main()
