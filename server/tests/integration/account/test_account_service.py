from __future__ import annotations

import os
import unittest

from src.business_logic.services.account_service import AccountService
from src.business_logic.managers.account import AccountManager
from src.db.account.mysql import MySQLAccountDB
from src.utils import ValidationError, AccountAlreadyExistsError
from src.api.errors import ApiError

from tests.helpers.integration_db import  ensure_tables_exist, reset_all_tables
from tests.helpers.integration_db_session import acquire, get_db, release


class TestAccountServiceIntegration(unittest.TestCase):
    """
    Integration tests:
      AccountService -> AccountManager -> MySQLAccountDB -> real MySQL (docker)
    """


    @classmethod
    def setUpClass(cls) -> None:
        # Make sure required env is set for imports / config
        os.environ.setdefault("SECRET_KEY", "test-secret")

        # Start/attach integration DB session (docker compose up / reuse)
        cls._session = acquire(timeout_s=120)
        cls._db = get_db()

        # Ensure schema exists once for this class, then start clean
        ensure_tables_exist(cls._db, timeout_s=60)
        reset_all_tables(cls._db)

        # Wire real DB -> manager -> service
        cls._account_db = MySQLAccountDB(db=cls._db)
        cls._manager = AccountManager(cls._account_db)
        cls._service = AccountService(cls._manager)

    @classmethod
    def tearDownClass(cls) -> None:
        release(cls._session, remove_volumes=False)


    # -----------------------------
    # create_account
    # -----------------------------
    def test_create_account_persists_and_returns_id(self) -> None:
        acc = self._service.create_account(
            email="a@umanitoba.ca",
            password="Password1",
            fname="John",
            lname="Smith",
        )

        self.assertIsNotNone(acc.id)

        # Verify it really exists in DB by fetching via DB layer
        in_db = self._account_db.get_by_email("a@umanitoba.ca")
        self.assertIsNotNone(in_db)
        self.assertEqual(in_db.email, "a@umanitoba.ca")
        self.assertEqual(in_db.password, "Password1")
        self.assertEqual(in_db.fname, "John")
        self.assertEqual(in_db.lname, "Smith")

    def test_create_account_duplicate_email_raises(self) -> None:
        self._service.create_account(
            email="dup@umanitoba.ca",
            password="Password1",
            fname="A",
            lname="B",
        )

        # Second insert should conflict at manager/service layer
        with self.assertRaises(AccountAlreadyExistsError):
            self._service.create_account(
                email="dup@umanitoba.ca",
                password="Password1",
                fname="A",
                lname="B",
            )

    def test_create_account_rejects_invalid_domain(self) -> None:
        with self.assertRaises(ValidationError):
            self._service.create_account(
                email="nope@gmail.com",
                password="Password1",
                fname="A",
                lname="B",
            )

    def test_create_account_rejects_weak_password(self) -> None:
        with self.assertRaises(ValidationError):
            self._service.create_account(
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
            self._service.login("x@umanitoba.ca", "Password1")
        self.assertEqual(ctx.exception.status_code, 401)
