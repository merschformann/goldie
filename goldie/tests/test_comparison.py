import json
import os
import tempfile
import unittest

from goldie.comparison import (
    ComparisonType,
    ConfigCompareJson,
    ConfigComparison,
    ConfigProcessJson,
    JsonReplacement,
    JsonRounding,
    compare_json,
    process_json,
)
from goldie.execution import ConfigRun, InputMode, OutputMode
from goldie.testing import ConfigFileTest, TestDefinition, run_file_unittest


class TestProcessJson(unittest.TestCase):
    def test_nested_lists_are_preserved(self):
        """Processing must not alter the structure of directly nested lists."""
        actual = [[{"a": 1, "b": 0.5}, {"c": 2}], [{"a": 3, "b": 0.5}]]
        processed = process_json(actual, ConfigProcessJson())
        self.assertEqual(processed, actual)

    def test_replacement(self):
        actual = [[{"a": 1, "duration": 0.5}], [{"a": 2, "duration": 0.7}]]
        configuration = ConfigProcessJson(
            replacements=[
                JsonReplacement(path="$[0][0].duration", value=0.123),
                JsonReplacement(path="$[1][0].duration", value=0.123),
            ]
        )
        processed = process_json(actual, configuration)
        self.assertEqual(processed, [[{"a": 1, "duration": 0.123}], [{"a": 2, "duration": 0.123}]])

    def test_replacement_without_root_marker(self):
        """Paths without the leading '$' are supported for convenience."""
        configuration = ConfigProcessJson(
            replacements=[
                JsonReplacement(path="data.random", value=3),
                JsonReplacement(path="data.list[1]", value=0),
            ]
        )
        processed = process_json({"data": {"random": 42, "list": [1, 2]}}, configuration)
        self.assertEqual(processed, {"data": {"random": 3, "list": [1, 0]}})

    def test_replacement_of_subtree(self):
        """A replacement path may point to a whole subtree instead of a leaf value."""
        actual = {"metrics": {"run": {"duration": 0.5, "start": "now"}}, "x": 1}
        configuration = ConfigProcessJson(replacements=[JsonReplacement(path="$.metrics.run", value="replaced")])
        processed = process_json(actual, configuration)
        self.assertEqual(processed, {"metrics": {"run": "replaced"}, "x": 1})

    def test_replacement_preserves_key_order(self):
        configuration = ConfigProcessJson(
            replacements=[JsonReplacement(path="$.b", value=0), JsonReplacement(path="$.c.d", value=0)]
        )
        processed = process_json({"a": 1, "b": 2, "c": {"d": 3, "e": 4}, "f": 5}, configuration)
        self.assertEqual(list(processed.keys()), ["a", "b", "c", "f"])
        self.assertEqual(list(processed["c"].keys()), ["d", "e"])

    def test_empty_containers_are_preserved(self):
        actual = {"options": {}, "assets": [], "data": {"x": 1}}
        self.assertEqual(process_json(actual, ConfigProcessJson()), actual)

    def test_replacement_does_not_match_sibling_prefix(self):
        """A replacement of '$.a' must not touch '$.ab'."""
        configuration = ConfigProcessJson(replacements=[JsonReplacement(path="$.a", value=0)])
        processed = process_json({"a": 1, "ab": 2}, configuration)
        self.assertEqual(processed, {"a": 0, "ab": 2})

    def test_replacement_missing_path_raises(self):
        """Replacing a path that does not exist must fail instead of silently adding it."""
        actual = [[{"metrics": {"run": {"duration": 0.5}}}]]
        configuration = ConfigProcessJson(replacements=[JsonReplacement(path="$[0].metrics.run.duration", value=0)])
        with self.assertRaisesRegex(ValueError, "not found"):
            process_json(actual, configuration)

    def test_rounding(self):
        configuration = ConfigProcessJson(roundings=[JsonRounding(path="$.a", precision=1)])
        self.assertEqual(process_json({"a": 1.26}, configuration), {"a": 1.3})

    def test_rounding_missing_path_raises(self):
        configuration = ConfigProcessJson(roundings=[JsonRounding(path="$.b", precision=1)])
        with self.assertRaisesRegex(ValueError, "not found"):
            process_json({"a": 1.26}, configuration)

    def test_rounding_non_number_raises(self):
        configuration = ConfigProcessJson(roundings=[JsonRounding(path="$.a", precision=1)])
        with self.assertRaisesRegex(ValueError, "Expected number"):
            process_json({"a": "foo"}, configuration)


class TestCompareJson(unittest.TestCase):
    def test_nested_vs_flat_list_differs(self):
        actual = [[{"a": 1}], [{"a": 2}]]
        expected = [{"a": 1}, {"a": 2}]
        equal, differences = compare_json(actual, expected, ConfigCompareJson())
        self.assertFalse(equal)
        self.assertTrue(differences)


class TestFileComparison(unittest.TestCase):
    """End-to-end comparison of a command output against a golden file."""

    def _run(self, output: object, golden: object, configuration: ConfigProcessJson = None):
        with tempfile.TemporaryDirectory() as directory:
            input_file = os.path.join(directory, "input.json")
            with open(input_file, "w") as f:
                json.dump(output, f)
            with open(input_file + ".golden", "w") as f:
                json.dump(golden, f)

            run_file_unittest(
                test=self,
                td=TestDefinition(input_file=input_file),
                configuration=ConfigFileTest(
                    run_configuration=ConfigRun(
                        # `cat` simply echoes stdin to stdout.
                        cmd="cat",
                        args=[],
                        cwd=directory,
                        input_mode=InputMode.STDIN,
                        output_mode=OutputMode.STDOUT,
                    ),
                    comparison_configuration=ConfigComparison(
                        comparison_type=ComparisonType.JSON,
                        json_processing_config=configuration,
                    ),
                ),
            )

    def test_nested_list_output_matches_nested_golden(self):
        output = [[{"a": 1, "duration": 0.5}], [{"a": 2, "duration": 0.7}]]
        golden = [[{"a": 1, "duration": 0.123}], [{"a": 2, "duration": 0.123}]]
        configuration = ConfigProcessJson(
            replacements=[JsonReplacement(path=f"$[{i}][0].duration", value=0.123) for i in range(2)]
        )
        self._run(output, golden, configuration)

    def test_nested_list_output_does_not_match_flat_golden(self):
        """Regression: nested lists were collapsed during processing, making them equal to a flat golden file."""
        output = [[{"a": 1}], [{"a": 2}]]
        golden = [{"a": 1}, {"a": 2}]
        with self.assertRaises(AssertionError):
            self._run(output, golden, ConfigProcessJson())

    def test_replacement_with_empty_value(self):
        """Processing is applied once only, so replacing with an empty container works too."""
        self._run({"a": {"b": 1}, "c": 2}, {"a": {}, "c": 2}, ConfigProcessJson([JsonReplacement("$.a", {})]))


if __name__ == "__main__":
    unittest.main()
