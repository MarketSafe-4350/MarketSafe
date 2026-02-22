from __future__ import annotations

import unittest

from tests.helpers.integration_db_session import suite_begin, suite_end
from tests.integration.account_db_manager import (
    TestMySQLAccountDB,
    TestAccountManagerIntegration,
)
from tests.integration.account_db_manager.test_account_service import (
    TestAccountServiceIntegration,
)
from tests.integration.db import TestDBUtility
from tests.helpers import IntegrationDBContext


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str
) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestDBUtility))
    suite.addTests(loader.loadTestsFromTestCase(TestMySQLAccountDB))
    suite.addTests(loader.loadTestsFromTestCase(TestAccountManagerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestAccountServiceIntegration))
    return suite


if __name__ == "__main__":
    # Start DB once for entire integration suite

    suite_begin(timeout_s=60)
    try:
        unittest.main(verbosity=2)

    finally:
        suite_end(remove_volumes=True)

    # it = IntegrationDBContext.up(timeout_s=60)
    #
    # try:
    #     unittest.main(verbosity=2)
    # finally:
    #     # Stop DB once after suite finishes
    #     it.down(remove_volumes=True)
