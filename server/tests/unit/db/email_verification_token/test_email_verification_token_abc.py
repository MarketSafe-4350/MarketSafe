from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from src.db import DBUtility
from src.domain_models import VerificationToken
from src.db.email_verification_token import EmailVerificationTokenDB


class _EmailVerificationTokenDBCoverageShim(EmailVerificationTokenDB):
    def add(self, token: VerificationToken) -> VerificationToken:
        return EmailVerificationTokenDB.add(self, token)

    def get_by_hash(self, token_hash: str):
        return EmailVerificationTokenDB.get_by_hash(self, token_hash)

    def get_latest_by_account(self, account_id: int):
        return EmailVerificationTokenDB.get_latest_by_account(self, account_id)

    def mark_used(self, token_id: int) -> None:
        return EmailVerificationTokenDB.mark_used(self, token_id)

    def clear_used_tokens(self, account_id: int) -> int:
        return EmailVerificationTokenDB.clear_used_tokens(self, account_id)  # type: ignore[return-value]


class TestEmailVerificationTokenDBABC(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock(spec=DBUtility)
        self.sut = _EmailVerificationTokenDBCoverageShim(self.db)

        now = datetime.utcnow()
        self.sample_token = VerificationToken(
            account_id=1,
            token_hash="hash123",
            expires_at=now + timedelta(hours=1),
            token_id=None,
            created_at=now,
            used=False,
            used_at=None,
        )

    # -----------------------------
    # __init__
    # -----------------------------
    def test_init_stores_db(self) -> None:
        self.assertIs(self.sut._db, self.db)

    def test_add_base_body_executes_and_returns_none(self) -> None:
        out = self.sut.add(self.sample_token)
        self.assertIsNone(out)

    def test_get_by_hash_base_body_executes_and_returns_none(self) -> None:
        out = self.sut.get_by_hash("hash123")
        self.assertIsNone(out)

    def test_get_latest_by_account_base_body_executes_and_returns_none(self) -> None:
        out = self.sut.get_latest_by_account(1)
        self.assertIsNone(out)

    def test_mark_used_base_body_executes(self) -> None:
        # Base is 'pass' -> just ensure it runs without exception
        self.sut.mark_used(1)

    def test_clear_used_tokens_base_body_executes_and_returns_none(self) -> None:
        out = self.sut.clear_used_tokens(1)
        self.assertIsNone(out)
