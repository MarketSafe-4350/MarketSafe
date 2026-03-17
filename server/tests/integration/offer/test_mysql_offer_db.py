from __future__ import annotations

import unittest
from uuid import uuid4

from src.db.account.mysql import MySQLAccountDB
from src.db.listing.mysql.mysql_listing_db import MySQLListingDB
from src.db.offer.mysql.mysql_offer_db import MySQLOfferDB
from src.domain_models.account import Account
from src.domain_models.listing import Listing
from src.domain_models.offer import Offer
from src.utils import ValidationError, DatabaseQueryError, OfferNotFoundError

from tests.helpers.integration_db import ensure_tables_exist, reset_all_tables
from tests.helpers.integration_db_session import acquire, get_db, release


class TestMySQLOfferDB(unittest.TestCase):
    """
    Integration tests: MySQLOfferDB -> real MySQL (docker)
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls._session = acquire(timeout_s=60)
        cls._db = get_db()

        cls._account_db = MySQLAccountDB(cls._db)
        cls._listing_db = MySQLListingDB(cls._db)
        cls._offer_db = MySQLOfferDB(cls._db)

        ensure_tables_exist(cls._db, timeout_s=60)
        reset_all_tables(cls._db)

    @classmethod
    def tearDownClass(cls) -> None:
        release(cls._session, remove_volumes=False)

    def setUp(self) -> None:
        reset_all_tables(self._db)

    # --------------------------------------------------
    # helpers
    # --------------------------------------------------

    def _create_account(self, prefix: str = "user") -> Account:
        uniq = uuid4().hex[:10]
        account = Account(
            email=f"{prefix}_{uniq}@example.com",
            password="pass",
            fname="Test",
            lname="User",
            verified=False,
        )
        created = self._account_db.add(account)
        self.assertIsNotNone(created.id)
        return created

    def _create_listing(self, seller_id: int) -> Listing:
        uniq = uuid4().hex[:10]
        listing = Listing(
            seller_id=seller_id,
            title=f"Title {uniq}",
            description=f"Desc {uniq}",
            price=100.0,
            location="Winnipeg",
            is_sold=False,
            sold_to_id=None,
        )
        created = self._listing_db.add(listing)
        self.assertIsNotNone(created.id)
        return created

    def _new_offer(
        self,
        listing_id: int,
        sender_id: int,
        price: float = 90.0,
        location: str | None = None,
    ) -> Offer:
        return Offer(
            listing_id=listing_id,
            sender_id=sender_id,
            offered_price=price,
            location_offered=location,
        )

    def _create_offer(self, listing_id: int, sender_id: int, price: float = 90.0) -> Offer:
        offer = self._offer_db.add(self._new_offer(listing_id, sender_id, price))
        self.assertIsNotNone(offer.id)
        return offer

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------

    def test_add_inserts_and_returns_id(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)

        offer = self._offer_db.add(self._new_offer(listing.id, buyer.id, price=75.0))

        self.assertIsNotNone(offer.id)
        self.assertEqual(offer.listing_id, listing.id)
        self.assertEqual(offer.sender_id, buyer.id)
        self.assertEqual(float(offer.offered_price), 75.0)
        self.assertFalse(bool(offer.seen))
        self.assertIsNone(offer.accepted)

    def test_add_none_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            self._offer_db.add(None)  # type: ignore[arg-type]

    def test_add_invalid_listing_fk_raises_database_query_error(self) -> None:
        seller = self._create_account("seller")
        offer = self._new_offer(listing_id=999999999, sender_id=seller.id)

        with self.assertRaises(DatabaseQueryError):
            self._offer_db.add(offer)

    def test_add_invalid_sender_fk_raises_database_query_error(self) -> None:
        seller = self._create_account("seller")
        listing = self._create_listing(seller.id)
        offer = self._new_offer(listing_id=listing.id, sender_id=999999999)

        with self.assertRaises(DatabaseQueryError):
            self._offer_db.add(offer)

    # --------------------------------------------------
    # READ
    # --------------------------------------------------

    def test_get_by_id_returns_offer(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)
        created = self._create_offer(listing.id, buyer.id)

        fetched = self._offer_db.get_by_id(created.id)

        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, created.id)
        self.assertEqual(fetched.listing_id, listing.id)
        self.assertEqual(fetched.sender_id, buyer.id)

    def test_get_by_id_returns_none_when_missing(self) -> None:
        result = self._offer_db.get_by_id(999999999)
        self.assertIsNone(result)

    def test_get_by_id_raises_validation_error_when_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self._offer_db.get_by_id(None)  # type: ignore[arg-type]

    def test_get_all_returns_all_offers(self) -> None:
        seller = self._create_account("seller")
        buyer1 = self._create_account("buyer1")
        buyer2 = self._create_account("buyer2")
        listing = self._create_listing(seller.id)

        o1 = self._create_offer(listing.id, buyer1.id)
        o2 = self._create_offer(listing.id, buyer2.id)

        offers = self._offer_db.get_all()
        ids = {o.id for o in offers}

        self.assertIn(o1.id, ids)
        self.assertIn(o2.id, ids)

    def test_get_all_returns_empty_when_no_offers(self) -> None:
        self.assertEqual(self._offer_db.get_all(), [])

    def test_get_by_listing_id_returns_offers_for_listing(self) -> None:
        seller = self._create_account("seller")
        buyer1 = self._create_account("buyer1")
        buyer2 = self._create_account("buyer2")
        listing1 = self._create_listing(seller.id)
        listing2 = self._create_listing(seller.id)

        o1 = self._create_offer(listing1.id, buyer1.id)
        o2 = self._create_offer(listing1.id, buyer2.id)
        _other = self._create_offer(listing2.id, buyer1.id)

        result = self._offer_db.get_by_listing_id(listing1.id)
        ids = {o.id for o in result}

        self.assertIn(o1.id, ids)
        self.assertIn(o2.id, ids)
        self.assertNotIn(_other.id, ids)

    def test_get_by_sender_id_returns_offers_by_sender(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        other_buyer = self._create_account("other")
        listing = self._create_listing(seller.id)

        o1 = self._create_offer(listing.id, buyer.id)
        _other = self._create_offer(listing.id, other_buyer.id)

        result = self._offer_db.get_by_sender_id(buyer.id)
        ids = {o.id for o in result}

        self.assertIn(o1.id, ids)
        self.assertNotIn(_other.id, ids)

    def test_get_accepted_by_listing_id_returns_only_accepted(self) -> None:
        seller = self._create_account("seller")
        buyer1 = self._create_account("buyer1")
        buyer2 = self._create_account("buyer2")
        listing = self._create_listing(seller.id)

        accepted = self._create_offer(listing.id, buyer1.id)
        pending = self._create_offer(listing.id, buyer2.id)

        self._offer_db.set_accepted(accepted.id, True)

        result = self._offer_db.get_accepted_by_listing_id(listing.id)
        ids = {o.id for o in result}

        self.assertIn(accepted.id, ids)
        self.assertNotIn(pending.id, ids)

    def test_get_unseen_by_listing_id_returns_only_unseen(self) -> None:
        seller = self._create_account("seller")
        buyer1 = self._create_account("buyer1")
        buyer2 = self._create_account("buyer2")
        listing = self._create_listing(seller.id)

        unseen = self._create_offer(listing.id, buyer1.id)
        seen = self._create_offer(listing.id, buyer2.id)

        self._offer_db.set_seen(seen.id)

        result = self._offer_db.get_unseen_by_listing_id(listing.id)
        ids = {o.id for o in result}

        self.assertIn(unseen.id, ids)
        self.assertNotIn(seen.id, ids)

    def test_get_pending_by_listing_id_returns_only_pending(self) -> None:
        seller = self._create_account("seller")
        buyer1 = self._create_account("buyer1")
        buyer2 = self._create_account("buyer2")
        listing = self._create_listing(seller.id)

        pending = self._create_offer(listing.id, buyer1.id)
        resolved = self._create_offer(listing.id, buyer2.id)

        self._offer_db.set_accepted(resolved.id, False)

        result = self._offer_db.get_pending_by_listing_id(listing.id)
        ids = {o.id for o in result}

        self.assertIn(pending.id, ids)
        self.assertNotIn(resolved.id, ids)

    def test_get_by_sender_and_listing_returns_offer(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)
        created = self._create_offer(listing.id, buyer.id)

        result = self._offer_db.get_by_sender_and_listing(buyer.id, listing.id)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, created.id)

    def test_get_by_sender_and_listing_returns_none_when_missing(self) -> None:
        result = self._offer_db.get_by_sender_and_listing(999999999, 999999999)
        self.assertIsNone(result)

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    def test_set_seen_marks_offer_as_seen(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)
        offer = self._create_offer(listing.id, buyer.id)

        self._offer_db.set_seen(offer.id)

        fetched = self._offer_db.get_by_id(offer.id)
        self.assertTrue(bool(fetched.seen))

    def test_set_seen_missing_raises_offer_not_found(self) -> None:
        with self.assertRaises(OfferNotFoundError):
            self._offer_db.set_seen(999999999)

    def test_set_seen_raises_validation_error_when_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self._offer_db.set_seen(None)  # type: ignore[arg-type]

    def test_set_accepted_accepts_offer(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)
        offer = self._create_offer(listing.id, buyer.id)

        self._offer_db.set_accepted(offer.id, True)

        fetched = self._offer_db.get_by_id(offer.id)
        self.assertTrue(bool(fetched.accepted))

    def test_set_accepted_rejects_offer(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)
        offer = self._create_offer(listing.id, buyer.id)

        self._offer_db.set_accepted(offer.id, False)

        fetched = self._offer_db.get_by_id(offer.id)
        self.assertFalse(bool(fetched.accepted))

    def test_set_accepted_missing_raises_offer_not_found(self) -> None:
        with self.assertRaises(OfferNotFoundError):
            self._offer_db.set_accepted(999999999, True)

    def test_set_accepted_raises_validation_error_when_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self._offer_db.set_accepted(None, True)  # type: ignore[arg-type]

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------

    def test_remove_deletes_offer_and_returns_true(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)
        offer = self._create_offer(listing.id, buyer.id)

        result = self._offer_db.remove(offer.id)

        self.assertTrue(result)
        self.assertIsNone(self._offer_db.get_by_id(offer.id))

    def test_remove_returns_false_when_not_found(self) -> None:
        result = self._offer_db.remove(999999999)
        self.assertFalse(result)

    def test_remove_raises_validation_error_when_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self._offer_db.remove(None)  # type: ignore[arg-type]
