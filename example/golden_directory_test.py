import unittest

import goldie


class TestExample(unittest.TestCase):
    def test_addition(self):
        config = goldie.directory.ConfigDirectoryTest(
            file_filter="data/*.json",
            run_configuration=goldie.ConfigRun(
                cmd="python",
                args=["script.py"],
                input_mode=goldie.InputMode.STDIN,
                output_mode=goldie.OutputMode.STDOUT,
            ),
            comparison_configuration=goldie.ConfigComparison(
                comparison_type=goldie.ComparisonType.JSON,
                json_processing_config=goldie.ConfigProcessJson(
                    replacements=[
                        goldie.JsonReplacement(
                            path="random",
                            value=3,
                        ),
                    ],
                ),
                json_comparison_config=goldie.ConfigCompareJson(),
            ),
        )
        goldie.directory.run_unittest(self, config)


if __name__ == "__main__":
    unittest.main()
