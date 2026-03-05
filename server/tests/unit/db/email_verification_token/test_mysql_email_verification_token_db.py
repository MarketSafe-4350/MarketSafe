from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from sqlalchemy.exc import SQLAlchemyError

from src.db import DBUtility
from src.db.email_verification_token.mysql.mysql_email_verification_token_db import (
    MySQLEmailVerificationTokenDB,
)
from src.domain_models import VerificationToken
from src.utils import DatabaseQueryError, TokenNotFoundError


class TestMySQLEmailVerificationTokenDB(unittest.TestCase):
    def setUp(self) -> None:
        self.db_util: MagicMock = MagicMock(spec=DBUtility)
        self.sut = MySQLEmailVerificationTokenDB(self.db_util)

        self.conn: MagicMock = MagicMock()

        self.connect_cm: MagicMock = MagicMock()
        self.connect_cm.__enter__.return_value = self.conn
        self.connect_cm.__exit__.return_value = False

        self.tx_cm: MagicMock = MagicMock()
        self.tx_cm.__enter__.return_value = self.conn
        self.tx_cm.__exit__.return_value = False

        self.db_util.connect.return_value = self.connect_cm
        self.db_util.transaction.return_value = self.tx_cm

    def _token(
        self,
        *,
        account_id: int = 1,
        token_hash: str = "hash123",
        token_id: int | None = None,
        created_at: datetime | None = None,
        expires_at: datetime | None = None,
        used: bool = False,
        used_at: datetime | None = None,
    ) -> VerificationToken:
        now = datetime.utcnow()
        return VerificationToken(
            account_id=account_id,
            token_hash=token_hash,
            expires_at=expires_at or (now + timedelta(hours=1)),
            token_id=token_id,
            created_at=created_at or now,
            used=used,
            used_at=used_at,
        )

    # -------------------------
    # add
    # -------------------------
    def test_add_inserts_and_returns_token_with_new_id(self) -> None:
        tok = self._token()

        exec_result = MagicMock()
        exec_result.lastrowid = 42
        self.conn.execute.return_value = exec_result

        out = self.sut.add(tok)

        self.db_util.transaction.assert_called_once()
        self.conn.execute.assert_called_once()

        self.assertEqual(out.id, 42)
        self.assertEqual(out.account_id, tok.account_id)
        self.assertEqual(out.token_hash, tok.token_hash)
        self.assertEqual(out.created_at, tok.created_at)
        self.assertEqual(out.expires_at, tok.expires_at)
        self.assertEqual(bool(out.used), bool(tok.used))
        self.assertEqual(out.used_at, tok.used_at)

    def test_add_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        tok = self._token()
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.add(tok)

    # -------------------------
    # get_by_hash
    # -------------------------
    def test_get_by_hash_returns_none_when_missing(self) -> None:
        exec_result = MagicMock()
        exec_result.mappings.return_value.first.return_value = None
        self.conn.execute.return_value = exec_result

        out = self.sut.get_by_hash("hash123")
        self.assertIsNone(out)

        self.db_util.connect.assert_called_once()
        self.conn.execute.assert_called_once()

    def test_get_by_hash_returns_token_when_found(self) -> None:
        now = datetime.utcnow()
        row = {
            "id": 7,
            "account_id": 2,
            "token_hash": "hashXYZ",
            "created_at": now,
            "expires_at": now + timedelta(hours=2),
            "used": 1,
            "used_at": now,
        }

        exec_result = MagicMock()
        exec_result.mappings.return_value.first.return_value = row
        self.conn.execute.return_value = exec_result

        out = self.sut.get_by_hash("hashXYZ")
        self.assertIsNotNone(out)
        self.assertEqual(out.id, 7)
        self.assertEqual(out.account_id, 2)
        self.assertEqual(out.token_hash, "hashXYZ")
        self.assertEqual(out.created_at, row["created_at"])
        self.assertEqual(out.expires_at, row["expires_at"])
        self.assertEqual(bool(out.used), True)
        self.assertEqual(out.used_at, row["used_at"])

    def test_get_by_hash_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.get_by_hash("hash123")

    # -------------------------
    # get_latest_by_account
    # -------------------------
    def test_get_latest_by_account_returns_none_when_missing(self) -> None:
        exec_result = MagicMock()
        exec_result.mappings.return_value.first.return_value = None
        self.conn.execute.return_value = exec_result

        out = self.sut.get_latest_by_account(123)
        self.assertIsNone(out)

    def test_get_latest_by_account_returns_token_when_found(self) -> None:
        now = datetime.utcnow()
        row = {
            "id": 99,
            "account_id": 123,
            "token_hash": "latestHash",
            "created_at": now,
            "expires_at": now + timedelta(hours=1),
            "used": 0,
            "used_at": None,
        }

        exec_result = MagicMock()
        exec_result.mappings.return_value.first.return_value = row
        self.conn.execute.return_value = exec_result

        out = self.sut.get_latest_by_account(123)
        self.assertIsNotNone(out)
        self.assertEqual(out.id, 99)
        self.assertEqual(out.account_id, 123)
        self.assertEqual(out.token_hash, "latestHash")
        self.assertEqual(bool(out.used), False)

    def test_get_latest_by_account_raises_database_query_error_on_sqlalchemy_error(
        self,
    ) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.get_latest_by_account(1)

    # -------------------------
    # mark_used
    # -------------------------
    def test_mark_used_updates_when_row_exists(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 1
        self.conn.execute.return_value = exec_result

        self.sut.mark_used(5)

        self.db_util.transaction.assert_called_once()
        self.conn.execute.assert_called_once()

    def test_mark_used_raises_token_not_found_when_rowcount_zero(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 0
        self.conn.execute.return_value = exec_result

        with self.assertRaises(TokenNotFoundError):
            self.sut.mark_used(999)

    def test_mark_used_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.mark_used(1)

    # -------------------------
    # clear_used_tokens
    # -------------------------
    def test_clear_used_tokens_returns_deleted_count(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 3
        self.conn.execute.return_value = exec_result

        out = self.sut.clear_used_tokens(10)
        self.assertEqual(out, 3)

        self.db_util.transaction.assert_called_once()
        self.conn.execute.assert_called_once()

    def test_clear_used_tokens_returns_zero_when_none_deleted(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 0
        self.conn.execute.return_value = exec_result

        out = self.sut.clear_used_tokens(10)
        self.assertEqual(out, 0)

    def test_clear_used_tokens_raises_database_query_error_on_sqlalchemy_error(
        self,
    ) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.clear_used_tokens(10)

    # -------------------------
    # _map_to_token
    # -------------------------
    def test_map_to_token_maps_fields_and_casts_used_bool(self) -> None:
        now = datetime.utcnow()
        row = {
            "id": 1,
            "account_id": 2,
            "token_hash": "h",
            "created_at": now,
            "expires_at": now + timedelta(hours=1),
            "used": 1,  # should become True
            "used_at": None,
        }

        tok = MySQLEmailVerificationTokenDB._map_to_token(row)
        self.assertEqual(tok.id, 1)
        self.assertEqual(tok.account_id, 2)
        self.assertEqual(tok.token_hash, "h")
        self.assertEqual(tok.created_at, now)
        self.assertEqual(tok.expires_at, row["expires_at"])
        self.assertTrue(tok.used)
        self.assertIsNone(tok.used_at)
