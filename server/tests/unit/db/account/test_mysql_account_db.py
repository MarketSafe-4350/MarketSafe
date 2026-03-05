from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.db.account.mysql import MySQLAccountDB
from src.db import DBUtility
from src.domain_models import Account
from src.utils import (
    AccountAlreadyExistsError,
    AccountNotFoundError,
    DatabaseQueryError,
)


class TestMySQLAccountDB(unittest.TestCase):
    def setUp(self) -> None:
        # DBUtility is a dependency; we mock it + the context managers it returns.
        self.db_util: MagicMock = MagicMock(spec=DBUtility)
        self.account_db = MySQLAccountDB(self.db_util)

        # Common mocks for connect()/transaction() context managers
        self.conn: MagicMock = MagicMock()
        self.connect_cm: MagicMock = MagicMock()
        self.connect_cm.__enter__.return_value = self.conn
        self.connect_cm.__exit__.return_value = False

        self.tx_cm: MagicMock = MagicMock()
        self.tx_cm.__enter__.return_value = self.conn
        self.tx_cm.__exit__.return_value = False

        self.db_util.connect.return_value = self.connect_cm
        self.db_util.transaction.return_value = self.tx_cm

    def _account(self, *, email: str = "test@example.com") -> Account:
        return Account(
            account_id=None,
            email=email,
            password="hashed",
            fname=" Test ",
            lname=" User ",
            verified=False,
        )

    # -----------------------------
    # add
    # -----------------------------
    def test_add_inserts_and_returns_account_with_new_id(self) -> None:
        acc = self._account(email="new@example.com")

        exec_result = MagicMock()
        exec_result.lastrowid = 123
        self.conn.execute.return_value = exec_result

        out = self.account_db.add(acc)

        self.assertEqual(out.id, 123)
        self.assertEqual(out.email, "new@example.com")
        self.assertEqual(out.password, "hashed")
        self.assertEqual(out.fname, "Test")  # stripped
        self.assertEqual(out.lname, "User")  # stripped
        self.assertEqual(bool(out.verified), False)

        self.db_util.transaction.assert_called_once()
        self.conn.execute.assert_called_once()

    def test_add_raises_account_already_exists_on_integrity_error(self) -> None:
        acc = self._account(email="exists@example.com")
        self.conn.execute.side_effect = IntegrityError("stmt", {}, Exception("dup"))

        with self.assertRaises(AccountAlreadyExistsError):
            self.account_db.add(acc)

    def test_add_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        acc = self._account(email="boom@example.com")
        self.conn.execute.side_effect = SQLAlchemyError("db fail")

        with self.assertRaises(DatabaseQueryError):
            self.account_db.add(acc)

    # -----------------------------
    # get_by_id
    # -----------------------------
    def test_get_by_id_returns_none_when_missing(self) -> None:
        # chain: conn.execute(...).mappings().first() -> None
        exec_result = MagicMock()
        exec_result.mappings.return_value.first.return_value = None
        self.conn.execute.return_value = exec_result

        out = self.account_db.get_by_id(999)
        self.assertIsNone(out)

        self.db_util.connect.assert_called_once()
        self.conn.execute.assert_called_once()

    def test_get_by_id_returns_account_when_found(self) -> None:
        row = {
            "id": 5,
            "email": "a@b.com",
            "password": "hashed",
            "fname": "A",
            "lname": "B",
            "verified": 1,
        }

        exec_result = MagicMock()
        exec_result.mappings.return_value.first.return_value = row
        self.conn.execute.return_value = exec_result

        out = self.account_db.get_by_id(5)
        self.assertIsNotNone(out)
        self.assertEqual(out.id, 5)
        self.assertEqual(out.email, "a@b.com")
        self.assertEqual(out.fname, "A")
        self.assertEqual(out.lname, "B")
        self.assertEqual(bool(out.verified), True)

    def test_get_by_id_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.account_db.get_by_id(1)

    # -----------------------------
    # get_by_email
    # -----------------------------
    def test_get_by_email_returns_none_when_missing(self) -> None:
        exec_result = MagicMock()
        exec_result.mappings.return_value.first.return_value = None
        self.conn.execute.return_value = exec_result

        out = self.account_db.get_by_email("TEST@EXAMPLE.COM")
        self.assertIsNone(out)

    def test_get_by_email_returns_account_when_found(self) -> None:
        row = {
            "id": 7,
            "email": "test@example.com",
            "password": "hashed",
            "fname": "T",
            "lname": "U",
            "verified": 0,
        }

        exec_result = MagicMock()
        exec_result.mappings.return_value.first.return_value = row
        self.conn.execute.return_value = exec_result

        out = self.account_db.get_by_email("TEST@EXAMPLE.COM")
        self.assertIsNotNone(out)
        self.assertEqual(out.id, 7)
        self.assertEqual(out.email, "test@example.com")

    def test_get_by_email_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.account_db.get_by_email("x@y.com")

    # -----------------------------
    # get_all
    # -----------------------------
    def test_get_all_returns_list(self) -> None:
        rows = [
            {
                "id": 1,
                "email": "a@b.com",
                "password": "p",
                "fname": "A",
                "lname": "B",
                "verified": 0,
            },
            {
                "id": 2,
                "email": "c@d.com",
                "password": "p2",
                "fname": "C",
                "lname": "D",
                "verified": 1,
            },
        ]

        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = rows
        self.conn.execute.return_value = exec_result

        out = self.account_db.get_all()
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0].id, 1)
        self.assertEqual(out[1].id, 2)

    def test_get_all_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.account_db.get_all()

    # -----------------------------
    # set_verified
    # -----------------------------
    def test_set_verified_updates_when_row_exists(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 1
        self.conn.execute.return_value = exec_result

        self.account_db.set_verified(10, True)

        self.db_util.transaction.assert_called_once()
        self.conn.execute.assert_called_once()

    def test_set_verified_raises_account_not_found_when_rowcount_zero(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 0
        self.conn.execute.return_value = exec_result

        with self.assertRaises(AccountNotFoundError):
            self.account_db.set_verified(999, True)

    def test_set_verified_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.account_db.set_verified(1, True)

    # -----------------------------
    # set_verified_by_email
    # -----------------------------
    def test_set_verified_by_email_updates_when_row_exists(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 1
        self.conn.execute.return_value = exec_result

        self.account_db.set_verified_by_email("a@b.com", False)

        self.db_util.transaction.assert_called_once()
        self.conn.execute.assert_called_once()

    def test_set_verified_by_email_raises_account_not_found_when_rowcount_zero(
        self,
    ) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 0
        self.conn.execute.return_value = exec_result

        with self.assertRaises(AccountNotFoundError):
            self.account_db.set_verified_by_email("missing@b.com", True)

    def test_set_verified_by_email_raises_database_query_error_on_sqlalchemy_error(
        self,
    ) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.account_db.set_verified_by_email("a@b.com", True)

    # -----------------------------
    # remove
    # -----------------------------
    def test_remove_returns_true_when_deleted(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 1
        self.conn.execute.return_value = exec_result

        out = self.account_db.remove(5)
        self.assertTrue(out)

    def test_remove_returns_false_when_missing(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 0
        self.conn.execute.return_value = exec_result

        out = self.account_db.remove(999)
        self.assertFalse(out)

    def test_remove_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.account_db.remove(1)
