from __future__ import annotations

import os
import unittest

from src.business_logic.services.account_service import AccountService
from src.business_logic.managers.account import AccountManager
from src.db.account.mysql import MySQLAccountDB
from src.domain_models import Account
from src.utils import ValidationError, AccountAlreadyExistsError
from src.api.errors import ApiError

from tests.helpers.integration_db import IntegrationDBContext


class TestAccountServiceIntegration(unittest.TestCase):
    """
    Integration tests:
      AccountService -> AccountManager -> MySQLAccountDB -> real MySQL (docker)
    """

    ctx: IntegrationDBContext
    service: AccountService
    account_db: MySQLAccountDB

    @classmethod
    def setUpClass(cls) -> None:
        # Make sure required env is set for imports / config
        os.environ.setdefault("SECRET_KEY", "test-secret")

        # Bring up docker + initialize DBUtility singleton
        cls.ctx = IntegrationDBContext.up(timeout_s=120)

        # Wire real persistence + manager + service (real DB)
        cls.account_db = MySQLAccountDB(db=cls.ctx.db)
        manager = AccountManager(cls.account_db)
        cls.service = AccountService(manager)

    @classmethod
    def tearDownClass(cls) -> None:
        # Clean up db rows (nice to do even if compose persists)
        try:
            cls.account_db.clear_db()
        except Exception:
            pass

        cls.ctx.down(remove_volumes=True)

    def setUp(self) -> None:
        # Ensure each test runs with a clean table
        self.account_db.clear_db()

    # -----------------------------
    # create_account
    # -----------------------------
    def test_create_account_persists_and_returns_id(self) -> None:
        acc = self.service.create_account(
            email="a@umanitoba.ca",
            password="Password1",
            fname="John",
            lname="Smith",
        )

        self.assertIsNotNone(acc.id)

        # Verify it really exists in DB by fetching via DB layer
        in_db = self.account_db.get_by_email("a@umanitoba.ca")
        self.assertIsNotNone(in_db)
        self.assertEqual(in_db.email, "a@umanitoba.ca")
        self.assertEqual(in_db.password, "Password1")
        self.assertEqual(in_db.fname, "John")
        self.assertEqual(in_db.lname, "Smith")

    def test_create_account_duplicate_email_raises(self) -> None:
        self.service.create_account(
            email="dup@umanitoba.ca",
            password="Password1",
            fname="A",
            lname="B",
        )

        # Second insert should conflict at manager/service layer
        with self.assertRaises(AccountAlreadyExistsError):
            self.service.create_account(
                email="dup@umanitoba.ca",
                password="Password1",
                fname="A",
                lname="B",
            )

    def test_create_account_rejects_invalid_domain(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.create_account(
                email="nope@gmail.com",
                password="Password1",
                fname="A",
                lname="B",
            )

    def test_create_account_rejects_weak_password(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.create_account(
                email="weak@umanitoba.ca",
                password="password",  # no uppercase + no number
                fname="A",
                lname="B",
            )

    # -----------------------------
    # login (currently mock logic)
    # -----------------------------
    def test_login_invalid_credentials_raises_401(self) -> None:
        with self.assertRaises(ApiError) as ctx:
            self.service.login("x@umanitoba.ca", "Password1")
        self.assertEqual(ctx.exception.status_code, 401)
