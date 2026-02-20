from __future__ import annotations

import unittest

from tests.unit.account_mangers import TestAccountManager, TestAccountService


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestAccountManager))
    suite.addTests(loader.loadTestsFromTestCase(TestAccountService))
    return suite


if __name__ == "__main__":

    unittest.main(verbosity=2)

