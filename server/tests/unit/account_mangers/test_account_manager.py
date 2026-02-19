from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from src.business_logic.managers.account import AccountManager
from src.db.account import AccountDB
from src.domain_models import Account
from src.utils import AccountAlreadyExistsError, AccountNotFoundError


class TestAccountManager(unittest.TestCase):
    def setUp(self) -> None:
        self.db: MagicMock = MagicMock(spec=AccountDB)
        self.manager = AccountManager(self.db)

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
    # create_account
    # -----------------------------
    def test_create_account_raises_if_email_exists(self) -> None:
        acc = self._account(email="exists@example.com")
        self.db.get_by_email.return_value = Account(
            account_id=1,
            email=acc.email,
            password="hashed",
            fname="X",
            lname="Y",
            verified=False,
        )

        with self.assertRaises(AccountAlreadyExistsError):
            self.manager.create_account(acc)

        self.db.add.assert_not_called()

    def test_create_account_delegates_add_with_normalized_account(self) -> None:
        acc = self._account(email="new@example.com")
        self.db.get_by_email.return_value = None

        created = Account(
            account_id=123,
            email="new@example.com",
            password="hashed",
            fname="Test",
            lname="User",
            verified=False,
        )
        self.db.add.return_value = created

        result = self.manager.create_account(acc)

        self.assertEqual(result, created)

        # Ensure manager performed uniqueness check
        self.db.get_by_email.assert_called_once_with("new@example.com")

        # Ensure add called once with an Account
        self.db.add.assert_called_once()
        inserted_account: Account = self.db.add.call_args[0][0]

        # The manager creates a NEW Account object and strips names
        self.assertIsNone(inserted_account.id)  # or inserted_account._id; depends on your Account API

        self.assertEqual(inserted_account.email, "new@example.com")
        self.assertEqual(inserted_account.password, "hashed")
        self.assertEqual(inserted_account.fname, "Test")
        self.assertEqual(inserted_account.lname, "User")
        self.assertEqual(bool(inserted_account.verified), False)

    def test_create_account_none_raises(self) -> None:
        with self.assertRaises(Exception):
            # your Validation likely raises ValidationError (AppError)
            self.manager.create_account(None)  # type: ignore[arg-type]

    # -----------------------------
    # get_account_by_id / email
    # -----------------------------
    def test_get_account_by_id_delegates(self) -> None:
        self.db.get_by_id.return_value = None
        out = self.manager.get_account_by_id(5)
        self.assertIsNone(out)
        self.db.get_by_id.assert_called_once_with(5)

    def test_get_account_by_email_delegates(self) -> None:
        self.db.get_by_email.return_value = None
        out = self.manager.get_account_by_email("TEST@EXAMPLE.COM")
        self.assertIsNone(out)

        # valid_email lowercases/strips; depends on your Validation
        # We'll just verify it called db.get_by_email once with a string.
        self.assertTrue(self.db.get_by_email.called)

    # -----------------------------
    # list_accounts
    # -----------------------------
    def test_list_accounts_delegates(self) -> None:
        self.db.get_all.return_value = []
        out = self.manager.list_accounts()
        self.assertEqual(out, [])
        self.db.get_all.assert_called_once()

    # -----------------------------
    # set_verified / set_verified_by_email
    # -----------------------------
    def test_set_verified_delegates(self) -> None:
        self.manager.set_verified(10, True)
        self.db.set_verified.assert_called_once_with(10, True)

    def test_set_verified_by_email_delegates(self) -> None:
        self.manager.set_verified_by_email("a@b.com", False)
        self.db.set_verified_by_email.assert_called_once()
        # We won't assert exact email normalization; just that it was called.

    # -----------------------------
    # delete_account
    # -----------------------------
    def test_delete_account_returns_db_value(self) -> None:
        self.db.remove.return_value = True
        out = self.manager.delete_account(9)
        self.assertTrue(out)
        self.db.remove.assert_called_once_with(9)

    # -----------------------------
    # require_account_by_id
    # -----------------------------
    def test_require_account_by_id_raises_when_missing(self) -> None:
        self.db.get_by_id.return_value = None
        with self.assertRaises(AccountNotFoundError):
            self.manager.require_account_by_id(999)

    def test_require_account_by_id_returns_when_found(self) -> None:
        acc = Account(
            account_id=7,
            email="x@y.com",
            password="hashed",
            fname="X",
            lname="Y",
            verified=False,
        )
        self.db.get_by_id.return_value = acc

        out = self.manager.require_account_by_id(7)
        self.assertEqual(out, acc)