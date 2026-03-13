from __future__ import annotations

import unittest

from tests.helpers.integration_db_session import suite_begin, suite_end
from tests.integration.account import (
    TestMySQLAccountDB,
    TestAccountManagerIntegration,
)
from tests.integration.account.test_account_service import (
    TestAccountServiceIntegration,
)
from tests.integration.db import TestDBUtility
from tests.helpers import IntegrationDBContext
from tests.integration.email_verification import (
    TestEmailVerificationServiceIntegration,
    TestMySQLEmailVerificationTokenDB,
)
from tests.integration.listing import (
    TestListingManagerIntegration,
    TestMySQLListingDB,
    TestListingRouteIntegration,
    TestListingServiceIntegration,
)

from tests.integration.comment import (
    TestMySQLCommentDB,
    TestCommentManagerIntegration,
    TestCommentServiceIntegration,
)
from tests.integration.rating import TestMySQLRatingDB, TestRatingManagerIntegration


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str
) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestDBUtility))
    suite.addTests(loader.loadTestsFromTestCase(TestMySQLAccountDB))
    suite.addTests(loader.loadTestsFromTestCase(TestAccountManagerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestAccountServiceIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestListingManagerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestListingRouteIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestListingServiceIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestMySQLListingDB))
    suite.addTests(loader.loadTestsFromTestCase(TestMySQLCommentDB))
    suite.addTests(loader.loadTestsFromTestCase(TestCommentManagerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestCommentServiceIntegration))
    suite.addTests(
        loader.loadTestsFromTestCase(TestEmailVerificationServiceIntegration)
    )
    suite.addTests(loader.loadTestsFromTestCase(TestMySQLEmailVerificationTokenDB))
    suite.addTests(loader.loadTestsFromTestCase(TestMySQLRatingDB))
    suite.addTests(loader.loadTestsFromTestCase(TestRatingManagerIntegration))

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
