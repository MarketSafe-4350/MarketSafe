from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy.exc import OperationalError

from src.utils import DatabaseUnavailableError, ConfigurationError
from src.db.utils.db_utils import DBUtility


PATCH_TARGET = "src.db.utils.db_utils.create_engine"


class TestDBUtility(unittest.TestCase):
    def setUp(self) -> None:
        DBUtility.reset()

    def tearDown(self) -> None:
        DBUtility.reset()

    def _make_operational_error(self) -> OperationalError:
        return OperationalError("SELECT 1", {}, Exception("db down"))

    # -----------------------------
    # initialize / instance / reset
    # -----------------------------
    def test_initialize_sets_singleton_instance(self) -> None:
        with patch(PATCH_TARGET) as create_engine_mock:
            fake_engine = MagicMock()
            create_engine_mock.return_value = fake_engine

            DBUtility.initialize(
                host="localhost",
                port=3306,
                database="marketplace",
                username="root",
                password="pass",
            )

            inst = DBUtility.instance()
            self.assertIsInstance(inst, DBUtility)
            self.assertIs(inst.engine, fake_engine)

    def test_initialize_twice_raises_runtime_error(self) -> None:
        with patch(PATCH_TARGET) as create_engine_mock:
            create_engine_mock.return_value = MagicMock()

            DBUtility.initialize(
                host="localhost",
                port=3306,
                database="marketplace",
                username="root",
                password="pass",
            )

            with self.assertRaises(RuntimeError):
                DBUtility.initialize(
                    host="localhost",
                    port=3306,
                    database="marketplace",
                    username="root",
                    password="pass",
                )

    def test_instance_raises_configuration_error_when_not_initialized(self) -> None:
        with self.assertRaises(ConfigurationError):
            DBUtility.instance()

    def test_reset_disposes_engine_and_clears_singleton(self) -> None:
        with patch(PATCH_TARGET) as create_engine_mock:
            fake_engine = MagicMock()
            create_engine_mock.return_value = fake_engine

            DBUtility.initialize(
                host="localhost",
                port=3306,
                database="marketplace",
                username="root",
                password="pass",
            )

            DBUtility.reset()

            fake_engine.dispose.assert_called_once()
            with self.assertRaises(ConfigurationError):
                DBUtility.instance()

    def test_reset_handles_engine_dispose_exception(self) -> None:
        with patch(PATCH_TARGET) as create_engine_mock:
            fake_engine = MagicMock()

            # Make dispose raise an exception
            fake_engine.dispose.side_effect = Exception("dispose failure")

            create_engine_mock.return_value = fake_engine

            DBUtility.initialize(
                host="localhost",
                port=3306,
                database="marketplace",
                username="root",
                password="pass",
            )

            DBUtility.reset()

            self.assertIsNone(DBUtility._instance)

    def test_reset_is_safe_when_not_initialized(self) -> None:
        DBUtility.reset()

    # -----------------------------
    # __init__ creates engine with expected URL
    # -----------------------------
    def test_init_builds_engine_url(self) -> None:
        with patch(PATCH_TARGET) as create_engine_mock:
            fake_engine = MagicMock()
            create_engine_mock.return_value = fake_engine

            DBUtility(
                host="db",
                port=3306,
                database="marketplace",
                username="root",
                password="pass",
                driver="mysql+pymysql",
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True,
            )

            args, kwargs = create_engine_mock.call_args
            self.assertEqual(args[0], "mysql+pymysql://root:pass@db:3306/marketplace")
            self.assertEqual(kwargs.get("future"), True)
            self.assertEqual(kwargs.get("pool_pre_ping"), True)

    # -----------------------------
    # connect()
    # -----------------------------
    def test_connect_yields_connection_on_success(self) -> None:
        with patch(PATCH_TARGET) as create_engine_mock:
            fake_engine = MagicMock()
            create_engine_mock.return_value = fake_engine

            conn = MagicMock()
            engine_cm = MagicMock()
            engine_cm.__enter__.return_value = conn
            engine_cm.__exit__.return_value = False
            fake_engine.connect.return_value = engine_cm

            dbu = DBUtility(
                host="localhost",
                port=3306,
                database="marketplace",
                username="root",
                password="pass",
            )

            with dbu.connect() as c:
                self.assertIs(c, conn)

            fake_engine.connect.assert_called_once()

    def test_connect_converts_operational_error_to_database_unavailable(self) -> None:
        with patch(PATCH_TARGET) as create_engine_mock:
            fake_engine = MagicMock()
            create_engine_mock.return_value = fake_engine

            engine_cm = MagicMock()
            engine_cm.__enter__.side_effect = self._make_operational_error()
            engine_cm.__exit__.return_value = False
            fake_engine.connect.return_value = engine_cm

            dbu = DBUtility(
                host="localhost",
                port=3306,
                database="marketplace",
                username="root",
                password="pass",
            )

            with self.assertRaises(DatabaseUnavailableError):
                with dbu.connect():
                    pass

    # -----------------------------
    # transaction()
    # -----------------------------
    def test_transaction_yields_connection_on_success(self) -> None:
        with patch(PATCH_TARGET) as create_engine_mock:
            fake_engine = MagicMock()
            create_engine_mock.return_value = fake_engine

            conn = MagicMock()
            engine_cm = MagicMock()
            engine_cm.__enter__.return_value = conn
            engine_cm.__exit__.return_value = False
            fake_engine.begin.return_value = engine_cm

            dbu = DBUtility(
                host="localhost",
                port=3306,
                database="marketplace",
                username="root",
                password="pass",
            )

            with dbu.transaction() as c:
                self.assertIs(c, conn)

            fake_engine.begin.assert_called_once()

    def test_transaction_converts_operational_error_to_database_unavailable(
        self,
    ) -> None:
        with patch(PATCH_TARGET) as create_engine_mock:
            fake_engine = MagicMock()
            create_engine_mock.return_value = fake_engine

            engine_cm = MagicMock()
            engine_cm.__enter__.side_effect = self._make_operational_error()
            engine_cm.__exit__.return_value = False
            fake_engine.begin.return_value = engine_cm

            dbu = DBUtility(
                host="localhost",
                port=3306,
                database="marketplace",
                username="root",
                password="pass",
            )

            with self.assertRaises(DatabaseUnavailableError):
                with dbu.transaction():
                    pass

    # -----------------------------
    # dispose + properties
    # -----------------------------
    def test_dispose_calls_engine_dispose(self) -> None:
        with patch(PATCH_TARGET) as create_engine_mock:
            fake_engine = MagicMock()
            create_engine_mock.return_value = fake_engine

            dbu = DBUtility(
                host="localhost",
                port=3306,
                database="marketplace",
                username="root",
                password="pass",
            )

            dbu.dispose()
            fake_engine.dispose.assert_called_once()

    def test_properties_engine_and_database(self) -> None:
        with patch(PATCH_TARGET) as create_engine_mock:
            fake_engine = MagicMock()
            create_engine_mock.return_value = fake_engine

            dbu = DBUtility(
                host="localhost",
                port=3306,
                database="marketplace",
                username="root",
                password="pass",
            )

            self.assertIs(dbu.engine, fake_engine)
            self.assertEqual(dbu.database, "marketplace")
            self.assertEqual(dbu.url_database, "marketplace")
