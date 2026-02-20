from __future__ import annotations

import os
import threading
import unittest

from tests.integration.account_db_manager import TestMySQLAccountDB


def run_until_failure(testcase: type[unittest.TestCase], max_iters: int = 1_000_000) -> None:
    print(f"PID={os.getpid()} TID={threading.get_ident()}")
    loader = unittest.TestLoader()

    for i in range(1, max_iters + 1):
        suite = unittest.TestSuite()
        suite.addTests(loader.loadTestsFromTestCase(testcase))

        result = unittest.TestResult()
        suite.run(result)

        if result.wasSuccessful():
            if i % 20 == 0:
                print(f"[OK] iteration={i}")
            continue

        print(f"\n[FAILED] iteration={i}  testcase={testcase.__name__}")

        for test, err in result.failures:
            print("\n--- FAILURE ---")
            print(test)
            print(err)

        for test, err in result.errors:
            print("\n--- ERROR ---")
            print(test)
            print(err)

        return

    print(f"\nNo failures after {max_iters} iterations.")


if __name__ == "__main__":
    # Change this to the exact flaky test you want to hammer
    run_until_failure(
        TestMySQLAccountDB,
        max_iters=1_000_000,
    )
