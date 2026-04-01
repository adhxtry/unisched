import unittest

from unisched import print_hello


class TestMain(unittest.TestCase):
    def test_print_hello(self):
        self.assertTrue(print_hello())


if __name__ == "__main__":
    unittest.main()
