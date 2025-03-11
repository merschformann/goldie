import unittest

import goldie.comparison
import goldie.directory
import goldie.execution


class TestExample(unittest.TestCase):
    def test_addition(self):
        config = goldie.directory.ConfigDirectoryTest(
            file_filter="data/*.json",
            run_configuration=goldie.execution.ConfigRun(
                cmd="cat",
                args=["{input}"],
                input_mode=goldie.execution.InputMode.NONE,
                output_mode=goldie.execution.OutputMode.STDOUT,
            ),
            run_validation_configuration=goldie.execution.ConfigRunValidation(),
            comparison_configuration=goldie.comparison.ConfigComparison(
                comparison_type=goldie.comparison.ComparisonType.JSON,
                json_processing_config=goldie.comparison.ConfigProcessJson(),
                json_comparison_config=goldie.comparison.ConfigCompareJson(),
            ),
        )
        goldie.directory.run_unittest(self, config)


if __name__ == "__main__":
    unittest.main()
