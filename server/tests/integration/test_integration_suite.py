from __future__ import annotations

import unittest

from tests.integration.account import TestMySQLAccountDB, TestAccountManagerIntegration
# Import the test classes so unittest can load them
from tests.integration.test_db_utility import TestDBUtility


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str) -> unittest.TestSuite:
    """
    Aggregates all integration test classes into one suite.
    """
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestDBUtility))
    suite.addTests(loader.loadTestsFromTestCase(TestMySQLAccountDB))
    suite.addTests(loader.loadTestsFromTestCase(TestAccountManagerIntegration))
    return suite


if __name__ == "__main__":
    unittest.main(verbosity=2)