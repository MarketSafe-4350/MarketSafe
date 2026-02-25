from __future__ import annotations

import unittest

from tests.unit.listing import TestListingManagerUnit, TestListingService
from tests.unit.account import TestAccountManager, TestAccountService
from tests.unit.comment import TestCommentManagerUnit
from tests.unit.token import TestTokenGenerator, TestAccountTokenService, TestJWTAuth


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str
) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestAccountManager))
    suite.addTests(loader.loadTestsFromTestCase(TestAccountService))
    suite.addTests(loader.loadTestsFromTestCase(TestListingService))
    suite.addTests(loader.loadTestsFromTestCase(TestListingManagerUnit))
    suite.addTest(loader.loadTestsFromTestCase(TestCommentManagerUnit))
    suite.addTests(loader.loadTestsFromTestCase(TestTokenGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestAccountTokenService))
    suite.addTests(loader.loadTestsFromTestCase(TestJWTAuth))
    return suite


if __name__ == "__main__":

    unittest.main(verbosity=2)
