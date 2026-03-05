from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from src.business_logic.managers.account import AccountManager, IAccountManager
from src.db.account import AccountDB
from src.db.listing import ListingDB
from src.domain_models import Account
from src.utils import (
    AccountAlreadyExistsError,
    AccountNotFoundError,
    ConfigurationError,
)


class TestAccountManagerUnit(unittest.TestCase):
    def setUp(self) -> None:
        self.db: MagicMock = MagicMock(spec=AccountDB)
        self.manager = AccountManager(self.db)

    def test_init_calls_super(self):
        with patch.object(
            IAccountManager, "__init__", return_value=None
        ) as parent_init:
            AccountManager(self.db)
            parent_init.assert_called_once_with(self.db, None)

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
        self.assertIsNone(
            inserted_account.id
        )  # or inserted_account._id; depends on your Account API

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

    # -----------------------------
    # get_account_with_listings
    # -----------------------------
    def test_get_account_with_listings_raises_when_listing_db_missing(self) -> None:
        mgr = AccountManager(account_db=self.db, listing_db=None)

        with self.assertRaises(ConfigurationError):
            mgr.get_account_with_listings(1)

    def test_get_account_with_listings_returns_none_when_account_missing(self) -> None:
        listing_db = MagicMock(spec=ListingDB)
        mgr = AccountManager(account_db=self.db, listing_db=listing_db)

        self.db.get_by_id.return_value = None

        out = mgr.get_account_with_listings(5)
        self.assertIsNone(out)

        self.db.get_by_id.assert_called_once_with(5)
        listing_db.get_by_seller_id.assert_not_called()

    def test_get_account_with_listings_attaches_listings_and_returns_account(
        self,
    ) -> None:
        listing_db = MagicMock(spec=ListingDB)
        mgr = AccountManager(account_db=self.db, listing_db=listing_db)

        # account returned from account_db
        acc = MagicMock(spec=Account)
        acc.id = 7  # manager uses account.id later in other wrappers
        self.db.get_by_id.return_value = acc

        # listings returned from listing_db
        l1 = MagicMock()
        l2 = MagicMock()
        listing_db.get_by_seller_id.return_value = [l1, l2]

        out = mgr.get_account_with_listings(7)

        self.assertIs(out, acc)
        listing_db.get_by_seller_id.assert_called_once_with(7)

        # ensure it attached via domain method
        self.assertEqual(acc.add_listing.call_count, 2)
        acc.add_listing.assert_any_call(l1)
        acc.add_listing.assert_any_call(l2)

    # -----------------------------
    # get_account_with_listings_by_email
    # -----------------------------
    def test_get_account_with_listings_by_email_returns_none_when_email_not_found(
        self,
    ) -> None:
        listing_db = MagicMock(spec=ListingDB)
        mgr = AccountManager(account_db=self.db, listing_db=listing_db)

        self.db.get_by_email.return_value = None

        out = mgr.get_account_with_listings_by_email("TEST@EXAMPLE.COM")
        self.assertIsNone(out)

        # Should have normalized email and queried account_db
        self.assertTrue(self.db.get_by_email.called)
        listing_db.get_by_seller_id.assert_not_called()

    def test_get_account_with_listings_by_email_delegates_when_found(self) -> None:
        listing_db = MagicMock(spec=ListingDB)
        mgr = AccountManager(account_db=self.db, listing_db=listing_db)

        acc = MagicMock(spec=Account)
        acc.id = 10
        self.db.get_by_email.return_value = acc

        with patch.object(mgr, "get_account_with_listings", return_value=acc) as gwl:
            out = mgr.get_account_with_listings_by_email("test@example.com")

        self.assertIs(out, acc)
        gwl.assert_called_once_with(10)

    # -----------------------------
    # get_account_with_listings_for
    # -----------------------------
    def test_get_account_with_listings_for_raises_when_account_none(self) -> None:
        listing_db = MagicMock(spec=ListingDB)
        mgr = AccountManager(account_db=self.db, listing_db=listing_db)

        with self.assertRaises(Exception):
            mgr.get_account_with_listings_for(None)  # type: ignore[arg-type]

    def test_get_account_with_listings_for_returns_none_when_account_unpersisted(
        self,
    ) -> None:
        listing_db = MagicMock(spec=ListingDB)
        mgr = AccountManager(account_db=self.db, listing_db=listing_db)

        acc = MagicMock(spec=Account)
        acc.id = None  # unpersisted

        out = mgr.get_account_with_listings_for(acc)
        self.assertIsNone(out)

    def test_get_account_with_listings_for_delegates_when_account_has_id(self) -> None:
        listing_db = MagicMock(spec=ListingDB)
        mgr = AccountManager(account_db=self.db, listing_db=listing_db)

        acc = MagicMock(spec=Account)
        acc.id = 77

        with patch.object(mgr, "get_account_with_listings", return_value=acc) as gwl:
            out = mgr.get_account_with_listings_for(acc)

        self.assertIs(out, acc)
        gwl.assert_called_once_with(77)
