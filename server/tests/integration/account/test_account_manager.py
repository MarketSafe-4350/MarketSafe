from __future__ import annotations

import unittest
from uuid import uuid4

from src.business_logic.managers.account import AccountManager
from src.db.account.mysql import MySQLAccountDB
from src.db.listing.mysql import MySQLListingDB

from src.domain_models import Account, Listing
from src.utils import AccountAlreadyExistsError, AccountNotFoundError, ValidationError, ConfigurationError
from tests.helpers.integration_db import ensure_tables_exist, reset_all_tables

from tests.helpers.integration_db_session import acquire, get_db, release


class TestAccountManagerIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:

        cls._session = acquire(timeout_s=60)
        cls._db = get_db()

        ensure_tables_exist(cls._db,  timeout_s=60)
        reset_all_tables(cls._db)

        cls._account_db = MySQLAccountDB(cls._db)
        cls._listing_db = MySQLListingDB(cls._db)
        cls._manager = AccountManager(cls._account_db, listing_db=cls._listing_db)

        cls._manager_no_listing = AccountManager(cls._account_db, listing_db=None)

    @classmethod
    def tearDownClass(cls) -> None:
        release(cls._session, remove_volumes=False)

    def _new_listing(self, seller_id: int) -> Listing:
        uniq = uuid4().hex[:10]
        return Listing(
            seller_id=seller_id,
            title=f"Title {uniq}",
            description=f"Desc {uniq}",
            price=100.0,
            location="Winnipeg",
        )
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
        self.assertIsNotNone(created, "Row missing immediately after insert -> cleanup/race/schema issue")

        self.assertIsNotNone(created.id)  # adjust if your property is account_id
        self.assertEqual(created.email, acc.email)

        fetched = self._manager.get_account_by_email(acc.email)
        self.assertIsNotNone(fetched, "Account disappeared after update (likely cleanup race)")

        self.assertIsNotNone(fetched)

    def test_create_account_duplicate_raises(self) -> None:
        acc = self._new_account()
        self._manager.create_account(acc)

        with self.assertRaises(AccountAlreadyExistsError):
            self._manager.create_account(acc)

    def test_set_verified_by_email_updates_row(self) -> None:
        acc = self._new_account()
        created = self._manager.create_account(acc)
        self.assertIsNotNone(created, "Row missing immediately after insert -> cleanup/race/schema issue")

        self._manager.set_verified_by_email(created.email, True)

        updated = self._manager.get_account_by_email(created.email)
        self.assertIsNotNone(updated, "Account disappeared after update (likely cleanup race)")

        self.assertIsNotNone(updated)
        self.assertIsNotNone(updated)
        self.assertTrue(bool(updated.verified))

    def test_get_account_with_listings_returns_account_and_listings(self) -> None:
        acc = self._new_account()
        created = self._manager.create_account(acc)
        self.assertIsNotNone(created.id)

        # Create 2 listings for this seller
        l1 = self._listing_db.add(self._new_listing(created.id))
        l2 = self._listing_db.add(self._new_listing(created.id))
        self.assertIsNotNone(l1.id)
        self.assertIsNotNone(l2.id)

        enriched = self._manager.get_account_with_listings(created.id)
        self.assertIsNotNone(enriched)
        assert enriched is not None

        listings = enriched.listings
        self.assertEqual(len(listings), 2)
        for li in listings:
            self.assertEqual(li.seller_id, created.id)

    def test_get_account_with_listings_returns_account_when_no_listings(self) -> None:
        created = self._manager.create_account(self._new_account())
        self.assertIsNotNone(created.id)

        enriched = self._manager.get_account_with_listings(created.id)
        self.assertIsNotNone(enriched)
        assert enriched is not None

        self.assertEqual(enriched.id, created.id)
        self.assertEqual(enriched.listings, [])  # should be empty, not None

    def test_get_account_with_listings_missing_account_returns_none(self) -> None:
        out = self._manager.get_account_with_listings(999999)
        self.assertIsNone(out)

    def test_get_account_with_listings_requires_listing_db_dependency(self) -> None:
        created = self._manager.create_account(self._new_account())
        self.assertIsNotNone(created.id)

        with self.assertRaises(ConfigurationError):
            self._manager_no_listing.get_account_with_listings(created.id)

    def test_get_account_with_listings_by_email_happy_path(self) -> None:
        created = self._manager.create_account(self._new_account())
        self.assertIsNotNone(created.id)

        # Create listing so we can verify it attaches through wrapper too
        self._listing_db.add(self._new_listing(created.id))

        enriched = self._manager.get_account_with_listings_by_email(created.email)
        self.assertIsNotNone(enriched)
        assert enriched is not None

        self.assertEqual(enriched.id, created.id)
        self.assertEqual(len(enriched.listings), 1)
        self.assertEqual(enriched.listings[0].seller_id, created.id)

    def test_get_account_with_listings_by_email_missing_returns_none(self) -> None:
        out = self._manager.get_account_with_listings_by_email("missing@example.com")
        self.assertIsNone(out)

    def test_get_account_with_listings_by_email_invalid_email_raises(self) -> None:
        with self.assertRaises(ValidationError):
            self._manager.get_account_with_listings_by_email("not-an-email")

    def test_get_account_with_listings_for_happy_path(self) -> None:
        created = self._manager.create_account(self._new_account())
        self.assertIsNotNone(created.id)

        self._listing_db.add(self._new_listing(created.id))
        self._listing_db.add(self._new_listing(created.id))

        enriched = self._manager.get_account_with_listings_for(created)
        self.assertIsNotNone(enriched)
        assert enriched is not None
        self.assertEqual(enriched.id, created.id)
        self.assertEqual(len(enriched.listings), 2)

    def test_get_account_with_listings_for_unpersisted_returns_none(self) -> None:
        # Not persisted: id=None
        acc = self._new_account()  # account_id=None in your helper
        out = self._manager.get_account_with_listings_for(acc)
        self.assertIsNone(out)

    def test_get_account_with_listings_for_none_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            self._manager.get_account_with_listings_for(None)  # type: ignore[arg-type]