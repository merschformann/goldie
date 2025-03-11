# goldie

A humble library greasing the gears of golden file tests.

## Installation

```bash
pip install goldie
```

## Example

This is an example of how to use `goldie` to test a script across multiple JSON files. The golden files will be used as a reference to compare the output of the script. Adding `GOLDIE_UPDATE=1` to the environment variables will update the golden files with the output of the script. Find the full example in the [`example`](example) directory.

```python
import unittest

import goldie


class TestExample(unittest.TestCase):
    def test_script(self):
        config = goldie.ConfigDirectoryTest(
            # We want to test all JSON files in the data directory.
            file_filter="data/*.json",
            run_configuration=goldie.ConfigRun(
                # We simply run the script in this directory.
                cmd="python",
                args=["script.py"],
                # The script reads from stdin and writes to stdout.
                input_mode=goldie.InputMode.STDIN,
                output_mode=goldie.OutputMode.STDOUT,
            ),
            comparison_configuration=goldie.ConfigComparison(
                # We want to leverage the JSON structure instead of comparing raw strings.
                comparison_type=goldie.ComparisonType.JSON,
                json_processing_config=goldie.ConfigProcessJson(
                    replacements=[
                        # We want to replace an unstable value with a stable one.
                        goldie.JsonReplacement(path="random", value=3),
                    ],
                ),
            ),
        )
        goldie.directory.run_unittest(self, config)


if __name__ == "__main__":
    unittest.main()
```
