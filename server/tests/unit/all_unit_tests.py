from __future__ import annotations

import unittest

from tests.integration.listing import TestMySQLListingDB
from tests.unit.listing import TestListingManagerUnit
from tests.unit.listings.test_listing_service import TestListingService
from tests.unit.account_mangers import TestAccountManager, TestAccountService


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str
) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestAccountManager))
    suite.addTests(loader.loadTestsFromTestCase(TestAccountService))
    suite.addTests(loader.loadTestsFromTestCase(TestListingService))
    suite.addTests(loader.loadTestsFromTestCase(TestListingManagerUnit))
    return suite


if __name__ == "__main__":

    unittest.main(verbosity=2)
