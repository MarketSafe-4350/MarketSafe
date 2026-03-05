from __future__ import annotations

import unittest

from tests.unit.auth_token import (
    TestTokenGenerator,
    TestJWTAuth,
    TestAccountTokenService,
)
from tests.unit.contracts import TestBusinessManagerContracts
from tests.unit.listing import (
    TestListingManagerUnit,
    TestListingServiceUnit,
    TestMySQLListingDB,
    TestListingDBABC,
)
from tests.unit.account import (
    TestAccountManager,
    TestAccountService,
    TestMySQLAccountDB,
    TestAccountDBABC,
)
from tests.unit.comment import (
    TestCommentManagerUnit,
    TestCommentServiceUnit,
    TestCommentDBABC,
)
from tests.unit.email_verification import (
    TestMySQLEmailVerificationTokenDB,
    TestEmailVerificationTokenDBABC,
)
from tests.unit.db_utils import TestDBUtility
from tests.unit.api import TestAPIDependencies, TestAPIError, TestListingRoutes
from tests.unit.domain_models import TestDomainModels
from tests.unit.config import TestConfig

from tests.unit.utils import TestValidation


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
    suite.addTests(loader.loadTestsFromTestCase(TestAccountDBABC))
    suite.addTests(loader.loadTestsFromTestCase(TestMySQLAccountDB))
    suite.addTests(loader.loadTestsFromTestCase(TestCommentDBABC))
    suite.addTests(loader.loadTestsFromTestCase(TestMySQLEmailVerificationTokenDB))
    suite.addTests(loader.loadTestsFromTestCase(TestEmailVerificationTokenDBABC))
    suite.addTests(loader.loadTestsFromTestCase(TestListingDBABC))
    suite.addTests(loader.loadTestsFromTestCase(TestMySQLListingDB))
    suite.addTests(loader.loadTestsFromTestCase(TestDBUtility))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIDependencies))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIError))
    suite.addTests(loader.loadTestsFromTestCase(TestListingRoutes))
    suite.addTests(loader.loadTestsFromTestCase(TestDomainModels))
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestValidation))
    return suite


if __name__ == "__main__":

    unittest.main(verbosity=2)
