from __future__ import annotations

import unittest

from tests.unit.test_main import TestMainUnit
from tests.unit.api import (
    TestAPIDependencies,
    TestAPIError,
    TestListingRoutes,
    TestCommentConverter,
    TestListingConverter,
    TestErrorHandlers,
    TestAccountRoutes,
)
from tests.unit.auth import TestJWTAuth
from tests.unit.business_logic import (
    TestAccountManagerUnit,
    TestAccountServiceUnit,
    TestAccountTokenService,
    TestListingManagerUnit,
    TestListingServiceUnit,
    TestCommentManagerUnit,
    TestCommentServiceUnit,
    TestBusinessManagerContracts,
)
from tests.unit.config import TestConfig
from tests.unit.db import (
    TestAccountDBABC,
    TestMySQLAccountDB,
    TestCommentDBABC,
    TestMySQLCommentDB,
    TestEmailVerificationTokenDBABC,
    TestMySQLEmailVerificationTokenDB,
    TestListingDBABC,
    TestMySQLListingDB,
    TestDBUtility,
    TestCommentMapper,
)
from tests.unit.domain_models import TestDomainModels
from tests.unit.utils import TestValidation, TestTokenGenerator


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str
) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestAccountManagerUnit))
    suite.addTests(loader.loadTestsFromTestCase(TestAccountServiceUnit))
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
    suite.addTests(loader.loadTestsFromTestCase(TestCommentConverter))
    suite.addTests(loader.loadTestsFromTestCase(TestListingConverter))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandlers))
    suite.addTests(loader.loadTestsFromTestCase(TestAccountRoutes))
    suite.addTests(loader.loadTestsFromTestCase(TestMySQLCommentDB))
    suite.addTests(loader.loadTestsFromTestCase(TestCommentMapper))
    suite.addTests(loader.loadTestsFromTestCase(TestMainUnit))
    return suite


if __name__ == "__main__":

    unittest.main(verbosity=2)
