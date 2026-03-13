from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from src.business_logic.managers.account import AccountManager, IAccountManager
from src.db.account import AccountDB
from src.db.listing import ListingDB
from src.db.rating import BaseRatingDB
from src.domain_models import Account, Listing
from src.utils import (
    AccountAlreadyExistsError,
    AccountNotFoundError,
    ConfigurationError,
)


class TestAccountManagerUnit(unittest.TestCase):
    def setUp(self) -> None:
        self.db: MagicMock = MagicMock(spec=AccountDB)
        self.listing_db: MagicMock = MagicMock(spec=ListingDB)
        self.rating_db: MagicMock = MagicMock(spec=BaseRatingDB)

        self.manager = AccountManager(self.db)
        self.manager_with_listing = AccountManager(self.db, self.listing_db)
        self.manager_with_rating = AccountManager(self.db, rating_db=self.rating_db)
        self.manager_with_listing_and_rating = AccountManager(
            self.db, self.listing_db, self.rating_db
        )

    def test_init_calls_super(self):
        with patch.object(
            IAccountManager, "__init__", return_value=None
        ) as parent_init:
            AccountManager(self.db)
            parent_init.assert_called_once_with(self.db, None, None)

    def _account(
        self,
        *,
        account_id: int | None = None,
        email: str = "test@example.com",
    ) -> Account:
        return Account(
            account_id=account_id,
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
        self.db.get_by_email.assert_called_once_with("new@example.com")
        self.db.add.assert_called_once()

        inserted_account: Account = self.db.add.call_args[0][0]
        self.assertIsNone(inserted_account.id)
        self.assertEqual(inserted_account.email, "new@example.com")
        self.assertEqual(inserted_account.password, "hashed")
        self.assertEqual(inserted_account.fname, "Test")
        self.assertEqual(inserted_account.lname, "User")
        self.assertEqual(bool(inserted_account.verified), False)

    def test_create_account_none_raises(self) -> None:
        with self.assertRaises(Exception):
            self.manager.create_account(None)  # type: ignore[arg-type]

    def test_create_account_populates_rating_values_when_rating_db_available(self) -> None:
        acc = self._account(email="new@example.com")
        created = self._account(account_id=123, email="new@example.com")

        self.db.get_by_email.return_value = None
        self.db.add.return_value = created
        self.rating_db.get_average_rating_by_account_id.return_value = 4.5
        self.rating_db.get_sum_of_ratings_received_by_account_id.return_value = 9

        out = self.manager_with_rating.create_account(acc)

        self.assertIs(out, created)
        self.assertEqual(out.average_rating_received, 4.5)
        self.assertEqual(out.sum_of_ratings_received, 9)
        self.rating_db.get_average_rating_by_account_id.assert_called_once_with(123)
        self.rating_db.get_sum_of_ratings_received_by_account_id.assert_called_once_with(123)

    # -----------------------------
    # get_account_by_id / email
    # -----------------------------
    def test_get_account_by_id_delegates(self) -> None:
        self.db.get_by_id.return_value = None
        out = self.manager.get_account_by_id(5)
        self.assertIsNone(out)
        self.db.get_by_id.assert_called_once_with(5)

    def test_get_account_by_id_populates_rating_values_when_rating_db_available(self) -> None:
        acc = self._account(account_id=5)
        self.db.get_by_id.return_value = acc
        self.rating_db.get_average_rating_by_account_id.return_value = 3.5
        self.rating_db.get_sum_of_ratings_received_by_account_id.return_value = 7

        out = self.manager_with_rating.get_account_by_id(5)

        self.assertIs(out, acc)
        self.assertEqual(out.average_rating_received, 3.5)
        self.assertEqual(out.sum_of_ratings_received, 7)

    def test_get_account_by_email_delegates(self) -> None:
        self.db.get_by_email.return_value = None
        out = self.manager.get_account_by_email("TEST@EXAMPLE.COM")
        self.assertIsNone(out)
        self.assertTrue(self.db.get_by_email.called)

    def test_get_account_by_email_populates_rating_values_when_rating_db_available(self) -> None:
        acc = self._account(account_id=8, email="test@example.com")
        self.db.get_by_email.return_value = acc
        self.rating_db.get_average_rating_by_account_id.return_value = 4.0
        self.rating_db.get_sum_of_ratings_received_by_account_id.return_value = 10

        out = self.manager_with_rating.get_account_by_email("TEST@EXAMPLE.COM")

        self.assertIs(out, acc)
        self.assertEqual(out.average_rating_received, 4.0)
        self.assertEqual(out.sum_of_ratings_received, 10)

    # -----------------------------
    # list_accounts
    # -----------------------------
    def test_list_accounts_delegates(self) -> None:
        self.db.get_all.return_value = []
        out = self.manager.list_accounts()
        self.assertEqual(out, [])
        self.db.get_all.assert_called_once()

    def test_list_accounts_populates_rating_values_when_rating_db_available(self) -> None:
        a1 = self._account(account_id=1, email="a1@example.com")
        a2 = self._account(account_id=2, email="a2@example.com")
        self.db.get_all.return_value = [a1, a2]

        self.rating_db.get_average_rating_by_account_id.side_effect = [4.5, 3.0]
        self.rating_db.get_sum_of_ratings_received_by_account_id.side_effect = [9, 6]

        out = self.manager_with_rating.list_accounts()

        self.assertEqual(out, [a1, a2])
        self.assertEqual(a1.average_rating_received, 4.5)
        self.assertEqual(a1.sum_of_ratings_received, 9)
        self.assertEqual(a2.average_rating_received, 3.0)
        self.assertEqual(a2.sum_of_ratings_received, 6)

    # -----------------------------
    # set_verified / set_verified_by_email
    # -----------------------------
    def test_set_verified_delegates(self) -> None:
        self.manager.set_verified(10, True)
        self.db.set_verified.assert_called_once_with(10, True)

    def test_set_verified_by_email_delegates(self) -> None:
        self.manager.set_verified_by_email("a@b.com", False)
        self.db.set_verified_by_email.assert_called_once()

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
        acc = self._account(account_id=7, email="x@y.com")
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
        mgr = AccountManager(account_db=self.db, listing_db=self.listing_db)

        self.db.get_by_id.return_value = None

        out = mgr.get_account_with_listings(5)
        self.assertIsNone(out)

        self.db.get_by_id.assert_called_once_with(5)
        self.listing_db.get_by_seller_id.assert_not_called()

    def test_get_account_with_listings_attaches_listings_and_returns_account(self) -> None:
        mgr = AccountManager(account_db=self.db, listing_db=self.listing_db)

        acc = MagicMock(spec=Account)
        acc.id = 7
        self.db.get_by_id.return_value = acc

        l1 = MagicMock()
        l2 = MagicMock()
        self.listing_db.get_by_seller_id.return_value = [l1, l2]

        out = mgr.get_account_with_listings(7)

        self.assertIs(out, acc)
        self.listing_db.get_by_seller_id.assert_called_once_with(7)
        self.assertEqual(acc.add_listing.call_count, 2)
        acc.add_listing.assert_any_call(l1)
        acc.add_listing.assert_any_call(l2)

    def test_get_account_with_listings_populates_rating_values_when_rating_db_available(self) -> None:
        acc = self._account(account_id=7)
        listing = Listing(
            seller_id=7,
            title="title",
            description="desc",
            price=10.0,
            listing_id=11,
            location="Winnipeg",
            comments=[],
        )

        self.db.get_by_id.return_value = acc
        self.listing_db.get_by_seller_id.return_value = [listing]
        self.rating_db.get_average_rating_by_account_id.return_value = 4.2
        self.rating_db.get_sum_of_ratings_received_by_account_id.return_value = 12

        out = self.manager_with_listing_and_rating.get_account_with_listings(7)

        self.assertIs(out, acc)
        self.assertEqual(out.average_rating_received, 4.2)
        self.assertEqual(out.sum_of_ratings_received, 12)
        self.assertEqual(len(out.listings), 1)
        self.assertEqual(out.listings[0].id, 11)

    # -----------------------------
    # get_account_with_listings_by_email
    # -----------------------------
    def test_get_account_with_listings_by_email_returns_none_when_email_not_found(self) -> None:
        mgr = AccountManager(account_db=self.db, listing_db=self.listing_db)

        self.db.get_by_email.return_value = None

        out = mgr.get_account_with_listings_by_email("TEST@EXAMPLE.COM")
        self.assertIsNone(out)

        self.assertTrue(self.db.get_by_email.called)
        self.listing_db.get_by_seller_id.assert_not_called()

    def test_get_account_with_listings_by_email_delegates_when_found(self) -> None:
        mgr = AccountManager(account_db=self.db, listing_db=self.listing_db)

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
        mgr = AccountManager(account_db=self.db, listing_db=self.listing_db)

        with self.assertRaises(Exception):
            mgr.get_account_with_listings_for(None)  # type: ignore[arg-type]

    def test_get_account_with_listings_for_returns_none_when_account_unpersisted(self) -> None:
        mgr = AccountManager(account_db=self.db, listing_db=self.listing_db)

        acc = MagicMock(spec=Account)
        acc.id = None

        out = mgr.get_account_with_listings_for(acc)
        self.assertIsNone(out)

    def test_get_account_with_listings_for_delegates_when_account_has_id(self) -> None:
        mgr = AccountManager(account_db=self.db, listing_db=self.listing_db)

        acc = MagicMock(spec=Account)
        acc.id = 77

        with patch.object(mgr, "get_account_with_listings", return_value=acc) as gwl:
            out = mgr.get_account_with_listings_for(acc)

        self.assertIs(out, acc)
        gwl.assert_called_once_with(77)

    # -----------------------------
    # fill_account_rating_values
    # -----------------------------
    def test_fill_account_rating_values_raises_when_rating_db_missing(self) -> None:
        acc = self._account(account_id=5)

        with self.assertRaises(ConfigurationError):
            self.manager.fill_account_rating_values(acc)

    def test_fill_account_rating_values_returns_same_account_when_unpersisted(self) -> None:
        acc = self._account(account_id=None)

        out = self.manager_with_rating.fill_account_rating_values(acc)

        self.assertIs(out, acc)
        self.rating_db.get_average_rating_by_account_id.assert_not_called()
        self.rating_db.get_sum_of_ratings_received_by_account_id.assert_not_called()

    def test_fill_account_rating_values_populates_fields(self) -> None:
        acc = self._account(account_id=5)
        self.rating_db.get_average_rating_by_account_id.return_value = 4.8
        self.rating_db.get_sum_of_ratings_received_by_account_id.return_value = 15

        out = self.manager_with_rating.fill_account_rating_values(acc)

        self.assertIs(out, acc)
        self.assertEqual(out.average_rating_received, 4.8)
        self.assertEqual(out.sum_of_ratings_received, 15)
        self.rating_db.get_average_rating_by_account_id.assert_called_once_with(5)
        self.rating_db.get_sum_of_ratings_received_by_account_id.assert_called_once_with(5)

    # -----------------------------
    # get_account_with_rating_values_by_id
    # -----------------------------
    def test_get_account_with_rating_values_by_id_raises_when_rating_db_missing(self) -> None:
        with self.assertRaises(ConfigurationError):
            self.manager.get_account_with_rating_values_by_id(1)

    def test_get_account_with_rating_values_by_id_returns_none_when_missing(self) -> None:
        self.db.get_by_id.return_value = None

        out = self.manager_with_rating.get_account_with_rating_values_by_id(1)

        self.assertIsNone(out)
        self.db.get_by_id.assert_called_once_with(1)
        self.rating_db.get_average_rating_by_account_id.assert_not_called()

    def test_get_account_with_rating_values_by_id_populates_fields(self) -> None:
        acc = self._account(account_id=1)
        self.db.get_by_id.return_value = acc
        self.rating_db.get_average_rating_by_account_id.return_value = 4.1
        self.rating_db.get_sum_of_ratings_received_by_account_id.return_value = 8

        out = self.manager_with_rating.get_account_with_rating_values_by_id(1)

        self.assertIs(out, acc)
        self.assertEqual(out.average_rating_received, 4.1)
        self.assertEqual(out.sum_of_ratings_received, 8)

    # -----------------------------
    # get_account_with_rating_values_by_email
    # -----------------------------
    def test_get_account_with_rating_values_by_email_raises_when_rating_db_missing(self) -> None:
        with self.assertRaises(ConfigurationError):
            self.manager.get_account_with_rating_values_by_email("a@b.com")

    def test_get_account_with_rating_values_by_email_returns_none_when_missing(self) -> None:
        self.db.get_by_email.return_value = None

        out = self.manager_with_rating.get_account_with_rating_values_by_email("TEST@EXAMPLE.COM")

        self.assertIsNone(out)
        self.assertTrue(self.db.get_by_email.called)
        self.rating_db.get_average_rating_by_account_id.assert_not_called()

    def test_get_account_with_rating_values_by_email_populates_fields(self) -> None:
        acc = self._account(account_id=3, email="test@example.com")
        self.db.get_by_email.return_value = acc
        self.rating_db.get_average_rating_by_account_id.return_value = 5.0
        self.rating_db.get_sum_of_ratings_received_by_account_id.return_value = 20

        out = self.manager_with_rating.get_account_with_rating_values_by_email("TEST@EXAMPLE.COM")

        self.assertIs(out, acc)
        self.assertEqual(out.average_rating_received, 5.0)
        self.assertEqual(out.sum_of_ratings_received, 20)

    def test_get_account_by_id_with_rating_db_returns_unpersisted_account_without_populating_ratings(self) -> None:
        acc = self._account(account_id=None)
        self.db.get_by_id.return_value = acc

        out = self.manager_with_rating.get_account_by_id(5)

        self.assertIs(out, acc)
        self.assertIsNone(out.id)
        self.rating_db.get_average_rating_by_account_id.assert_not_called()
        self.rating_db.get_sum_of_ratings_received_by_account_id.assert_not_called()