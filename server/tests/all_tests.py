from __future__ import annotations

import sys
import unittest


# Import your existing suite modules (the ones you showed)
# Rename these imports to the REAL module paths in your project.
import tests.unit.all_unit_tests as unit_suite_module
import tests.integration.all_integration_tests as integration_suite_module
from tests.helpers.integration_db_session import suite_end, suite_begin


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str
) -> unittest.TestSuite:
    """
    Unittest discovery hook.
    Build ONE combined suite, using the two existing module loaders (no duplication).
    Unit suite first, then integration suite.
    """
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(unit_suite_module))
    suite.addTests(loader.loadTestsFromModule(integration_suite_module))
    return suite



if __name__ == "__main__":
    loader = unittest.TestLoader()
    runner = unittest.TextTestRunner(verbosity=2)

    # 1) UNIT
    unit_suite = loader.loadTestsFromModule(unit_suite_module)
    unit_result = runner.run(unit_suite)
    if not unit_result.wasSuccessful():
        sys.exit(1)

    # 2) INTEGRATION (DB up/down once)
    exit_code = 1
    suite_begin(timeout_s=60)
    try:
        integ_suite = loader.loadTestsFromModule(integration_suite_module)
        integ_result = runner.run(integ_suite)
        exit_code = 0 if integ_result.wasSuccessful() else 1
    finally:
        suite_end(remove_volumes=True)

    sys.exit(exit_code)