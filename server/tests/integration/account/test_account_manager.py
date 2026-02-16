from __future__ import annotations

import os
import unittest
from uuid import uuid4

from src.business_logic.managers.account import AccountManager
from src.db.account.mysql import MySQLAccountDB
from src.db.db_utils import DBUtility

from src.domain_models import Account
from src.utils import AccountAlreadyExistsError, AccountNotFoundError
from tests.helpers import IntegrationDBContext

from tests.helpers.docker_db import DockerComposeConfig, ensure_db_for_tests, down


class TestAccountManagerIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._it = IntegrationDBContext.up(timeout_s=60)
        cls._db = cls._it.db

        cls._account_db = MySQLAccountDB(cls._db)
        cls._manager = AccountManager(cls._account_db)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._it.down(remove_volumes=True)

    def setUp(self) -> None:
        # isolate tests
        self._account_db.clear_db()

    def _new_account(self) -> Account:
        uniq = uuid4().hex[:10]
        return Account(
            account_id=None,
            email=f"m_{uniq}@example.com",
            password="hashed_password",
            fname=" Test ",
            lname=" User ",
            verified=False,
        )

    def test_create_account_persists_and_returns_id(self) -> None:
        acc = self._new_account()
        created = self._manager.create_account(acc)

        self.assertIsNotNone(created.id)  # adjust if your property is account_id
        self.assertEqual(created.email, acc.email)

        fetched = self._manager.get_account_by_email(acc.email)
        self.assertIsNotNone(fetched)

    def test_create_account_duplicate_raises(self) -> None:
        acc = self._new_account()
        self._manager.create_account(acc)

        with self.assertRaises(AccountAlreadyExistsError):
            self._manager.create_account(acc)

    def test_set_verified_by_email_updates_row(self) -> None:
        acc = self._new_account()
        created = self._manager.create_account(acc)

        self._manager.set_verified_by_email(created.email, True)

        updated = self._manager.get_account_by_email(created.email)
        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertTrue(bool(updated.verified))

    def test_require_account_by_id_raises_when_missing(self) -> None:
        with self.assertRaises(AccountNotFoundError):
            self._manager.require_account_by_id(999999)