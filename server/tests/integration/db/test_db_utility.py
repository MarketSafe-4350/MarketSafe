from __future__ import annotations

import unittest

from sqlalchemy import text

from src.utils import DatabaseUnavailableError, DatabaseQueryError
from tests.helpers.integration_db import ensure_tables_exist, reset_all_tables

from tests.helpers.integration_db_session import acquire, get_db, release


class TestDBUtility(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._session = acquire(timeout_s=60)
        cls._db = get_db()

        ensure_tables_exist(cls._db, timeout_s=60)
        reset_all_tables(cls._db)

    @classmethod
    def tearDownClass(cls) -> None:
        release(cls._session, remove_volumes=False)

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