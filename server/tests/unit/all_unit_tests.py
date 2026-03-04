from __future__ import annotations

import unittest

from tests.unit.auth_token import TestTokenGenerator, TestJWTAuth, TestAccountTokenService
from tests.unit.contracts import TestBusinessManagerContracts
from tests.unit.listing import TestListingManagerUnit, TestListingServiceUnit
from tests.unit.account import TestAccountManager, TestAccountService
from tests.unit.comment import TestCommentManagerUnit, TestCommentServiceUnit
<<<<<<< 154-api-folder
from tests.unit.api import TestAPIDependencies, TestAPIError, TestListingRoutes

=======
from tests.unit.domain_models import TestDomainModels
>>>>>>> main


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str
) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestAccountManager))
    suite.addTests(loader.loadTestsFromTestCase(TestAccountService))
    suite.addTests(loader.loadTestsFromTestCase(TestListingServiceUnit))
    suite.addTests(loader.loadTestsFromTestCase(TestListingManagerUnit))
    suite.addTests(loader.loadTestsFromTestCase(TestCommentManagerUnit))
    suite.addTests(loader.loadTestsFromTestCase(TestCommentServiceUnit))
    suite.addTests(loader.loadTestsFromTestCase(TestTokenGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestAccountTokenService))
    suite.addTests(loader.loadTestsFromTestCase(TestJWTAuth))
    suite.addTests(loader.loadTestsFromTestCase(TestBusinessManagerContracts))
<<<<<<< 154-api-folder
    suite.addTests(loader.loadTestsFromTestCase(TestAPIDependencies))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIError))
    suite.addTests(loader.loadTestsFromTestCase(TestListingRoutes))

=======
    suite.addTests(loader.loadTestsFromTestCase(TestDomainModels))
>>>>>>> main
    return suite


if __name__ == "__main__":

    unittest.main(verbosity=2)
