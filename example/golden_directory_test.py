import unittest


class TestExample(unittest.TestCase):
    def test_addition(self):
        # Define a table of test cases
        test_cases = [
            (1, 2, 3),
            (-1, 1, 0),
            (0, 0, 0),
            (1234, 5678, 6912),
        ]

        # Iterate over the test cases
        for i, (a, b, expected) in enumerate(test_cases):
            with self.subTest(i=i, a=a, b=b, expected=expected):
                self.assertEqual(a + b, expected)


if __name__ == "__main__":
    unittest.main()
