from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from src.db.account import AccountDB
from src.db import DBUtility
from src.domain_models import Account


class _AccountDBCoverageShim(AccountDB):
    def add(self, account: Account) -> Account:
        return AccountDB.add(self, account)

    def get_by_id(self, account_id: int):
        return AccountDB.get_by_id(self, account_id)

    def get_by_email(self, email: str):
        return AccountDB.get_by_email(self, email)

    def get_all(self):
        return AccountDB.get_all(self)

    def set_verified(self, account_id: int, verified: bool) -> None:
        return AccountDB.set_verified(self, account_id, verified)

    def set_verified_by_email(self, email: str, verified: bool) -> None:
        return AccountDB.set_verified_by_email(self, email, verified)

    def remove(self, account_id: int) -> bool:
        return AccountDB.remove(self, account_id)


class TestAccountDBABC(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock(spec=DBUtility)
        self.sut = _AccountDBCoverageShim(self.db)

        self.sample_account = Account(
            account_id=None,
            email="test@example.com",
            password="hashed",
            fname="Test",
            lname="User",
            verified=False,
        )

    # -----------------------------
    # __init__
    # -----------------------------
    def test_init_stores_db(self) -> None:
        self.assertIs(self.sut._db, self.db)

    # -----------------------------
    # abstract methods: execute base bodies (raise NotImplementedError)
    # -----------------------------
    def test_add_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.add(self.sample_account)

    def test_get_by_id_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_by_id(1)

    def test_get_by_email_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_by_email("test@example.com")

    def test_get_all_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_all()

    def test_set_verified_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.set_verified(1, True)

    def test_set_verified_by_email_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.set_verified_by_email("test@example.com", True)

    def test_remove_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.remove(1)
