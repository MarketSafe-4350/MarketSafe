from __future__ import annotations

import os
import unittest

from sqlalchemy import text

from src.db.db_utils import DBUtility
from src.utils import DatabaseUnavailableError, DatabaseQueryError
from tests.helpers import IntegrationDBContext

from tests.helpers.docker_db import DockerComposeConfig, ensure_db_for_tests, down


class TestDBUtility(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._it = IntegrationDBContext.up(timeout_s=60)
        cls._db = cls._it.db

    @classmethod
    def tearDownClass(cls) -> None:
        cls._it.down(remove_volumes=True)

    def test_ping_select_1(self) -> None:
        try:
            with self._db.connect() as conn:
                val = conn.execute(text("SELECT 1")).scalar_one()
                self.assertEqual(val, 1)
        except DatabaseUnavailableError as e:
            self.fail(f"DB should be reachable, got DatabaseUnavailableError: {e}")
        except DatabaseQueryError as e:
            self.fail(f"Query should succeed, got DatabaseQueryError: {e}")

    def test_account_table_exists(self) -> None:
        try:
            with self._db.connect() as conn:
                cnt = conn.execute(text("SELECT COUNT(*) FROM account")).scalar_one()
                self.assertIsInstance(cnt, int)
                self.assertGreaterEqual(cnt, 0)
        except DatabaseUnavailableError as e:
            self.fail(f"DB should be reachable, got DatabaseUnavailableError: {e}")
        except DatabaseQueryError as e:
            self.fail(f"Query should succeed, got DatabaseQueryError: {e}")