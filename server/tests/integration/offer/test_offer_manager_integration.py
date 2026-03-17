from __future__ import annotations

import unittest
from uuid import uuid4

from src.business_logic.managers.offer.offer_manager import OfferManager
from src.db.account.mysql import MySQLAccountDB
from src.db.listing.mysql.mysql_listing_db import MySQLListingDB
from src.db.offer.mysql.mysql_offer_db import MySQLOfferDB
from src.domain_models.account import Account
from src.domain_models.listing import Listing
from src.domain_models.offer import Offer
from src.utils import (
    ConflictError,
    ListingNotFoundError,
    OfferNotFoundError,
    UnapprovedBehaviorError,
)

from tests.helpers.integration_db import ensure_tables_exist, reset_all_tables
from tests.helpers.integration_db_session import acquire, get_db, release


class TestOfferManagerIntegration(unittest.TestCase):
    """
    Integration tests: OfferManager -> MySQLOfferDB + MySQLListingDB -> real MySQL (docker)
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls._session = acquire(timeout_s=60)
        cls._db = get_db()

        cls._account_db = MySQLAccountDB(cls._db)
        cls._listing_db = MySQLListingDB(cls._db)
        cls._offer_db = MySQLOfferDB(cls._db)

        cls._mgr = OfferManager(cls._offer_db, cls._listing_db)

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
        created = self._account_db.add(Account(
            email=f"{prefix}_{uniq}@example.com",
            password="pass",
            fname="Test",
            lname="User",
            verified=False,
        ))
        self.assertIsNotNone(created.id)
        return created

    def _create_listing(self, seller_id: int, *, is_sold: bool = False, sold_to_id: int | None = None) -> Listing:
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
        if is_sold and sold_to_id:
            self._listing_db.set_sold(created.id, True, sold_to_id)
        return created

    def _create_offer(self, listing_id: int, sender_id: int, price: float = 90.0) -> Offer:
        offer = self._mgr.create_offer(Offer(
            listing_id=listing_id,
            sender_id=sender_id,
            offered_price=price,
        ))
        self.assertIsNotNone(offer.id)
        return offer

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------

    def test_create_offer_persists_and_returns_id(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)

        offer = self._mgr.create_offer(Offer(
            listing_id=listing.id,
            sender_id=buyer.id,
            offered_price=80.0,
        ))

        self.assertIsNotNone(offer.id)
        self.assertEqual(offer.listing_id, listing.id)
        self.assertEqual(offer.sender_id, buyer.id)

    def test_create_offer_raises_when_listing_not_found(self) -> None:
        buyer = self._create_account("buyer")

        with self.assertRaises(ListingNotFoundError):
            self._mgr.create_offer(Offer(
                listing_id=999999999,
                sender_id=buyer.id,
                offered_price=80.0,
            ))

    def test_create_offer_raises_when_listing_is_sold(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id, is_sold=True, sold_to_id=buyer.id)

        other_buyer = self._create_account("other")
        with self.assertRaises(UnapprovedBehaviorError):
            self._mgr.create_offer(Offer(
                listing_id=listing.id,
                sender_id=other_buyer.id,
                offered_price=80.0,
            ))

    def test_create_offer_raises_when_sender_is_seller(self) -> None:
        seller = self._create_account("seller")
        listing = self._create_listing(seller.id)

        with self.assertRaises(UnapprovedBehaviorError):
            self._mgr.create_offer(Offer(
                listing_id=listing.id,
                sender_id=seller.id,
                offered_price=80.0,
            ))

    def test_create_offer_raises_conflict_when_pending_offer_exists(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)

        self._create_offer(listing.id, buyer.id)

        with self.assertRaises(ConflictError):
            self._mgr.create_offer(Offer(
                listing_id=listing.id,
                sender_id=buyer.id,
                offered_price=95.0,
            ))

    def test_create_offer_allows_resubmission_after_rejection(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)

        first = self._create_offer(listing.id, buyer.id, price=80.0)
        self._offer_db.set_accepted(first.id, False)

        second = self._mgr.create_offer(Offer(
            listing_id=listing.id,
            sender_id=buyer.id,
            offered_price=90.0,
        ))

        self.assertIsNotNone(second.id)
        self.assertNotEqual(first.id, second.id)

    # --------------------------------------------------
    # READ (simple)
    # --------------------------------------------------

    def test_get_offer_by_id_returns_offer(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)
        created = self._create_offer(listing.id, buyer.id)

        fetched = self._mgr.get_offer_by_id(created.id)

        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, created.id)

    def test_get_all_offers_returns_all(self) -> None:
        seller = self._create_account("seller")
        buyer1 = self._create_account("buyer1")
        buyer2 = self._create_account("buyer2")
        listing = self._create_listing(seller.id)

        o1 = self._create_offer(listing.id, buyer1.id)
        o2 = self._create_offer(listing.id, buyer2.id)

        all_offers = self._mgr.get_all_offers()
        ids = {o.id for o in all_offers}

        self.assertIn(o1.id, ids)
        self.assertIn(o2.id, ids)

    def test_get_offers_by_listing_id(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing1 = self._create_listing(seller.id)
        listing2 = self._create_listing(seller.id)

        o1 = self._create_offer(listing1.id, buyer.id)
        _other = self._create_offer(listing2.id, buyer.id)

        result = self._mgr.get_offers_by_listing_id(listing1.id)
        ids = {o.id for o in result}

        self.assertIn(o1.id, ids)
        self.assertNotIn(_other.id, ids)

    def test_get_offers_by_sender_id(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        other_buyer = self._create_account("other")
        listing1 = self._create_listing(seller.id)
        listing2 = self._create_listing(seller.id)

        o1 = self._create_offer(listing1.id, buyer.id)
        _other = self._create_offer(listing2.id, other_buyer.id)

        result = self._mgr.get_offers_by_sender_id(buyer.id)
        ids = {o.id for o in result}

        self.assertIn(o1.id, ids)
        self.assertNotIn(_other.id, ids)

    # --------------------------------------------------
    # READ (aggregated)
    # --------------------------------------------------

    def test_get_offers_sellers_aggregates_across_all_listings(self) -> None:
        seller = self._create_account("seller")
        buyer1 = self._create_account("buyer1")
        buyer2 = self._create_account("buyer2")
        listing1 = self._create_listing(seller.id)
        listing2 = self._create_listing(seller.id)

        o1 = self._create_offer(listing1.id, buyer1.id)
        o2 = self._create_offer(listing2.id, buyer2.id)

        result = self._mgr.get_offers_sellers(seller.id)
        ids = {o.id for o in result}

        self.assertIn(o1.id, ids)
        self.assertIn(o2.id, ids)

    def test_get_offer_sellers_pending_returns_only_pending(self) -> None:
        seller = self._create_account("seller")
        buyer1 = self._create_account("buyer1")
        buyer2 = self._create_account("buyer2")
        listing = self._create_listing(seller.id)

        pending = self._create_offer(listing.id, buyer1.id)
        rejected = self._create_offer(listing.id, buyer2.id)
        self._offer_db.set_accepted(rejected.id, False)

        result = self._mgr.get_offer_sellers_pending(seller.id)
        ids = {o.id for o in result}

        self.assertIn(pending.id, ids)
        self.assertNotIn(rejected.id, ids)

    def test_get_offer_sellers_unseen_returns_only_unseen(self) -> None:
        seller = self._create_account("seller")
        buyer1 = self._create_account("buyer1")
        buyer2 = self._create_account("buyer2")
        listing = self._create_listing(seller.id)

        unseen = self._create_offer(listing.id, buyer1.id)
        seen = self._create_offer(listing.id, buyer2.id)
        self._offer_db.set_seen(seen.id)

        result = self._mgr.get_offer_sellers_unseen(seller.id)
        ids = {o.id for o in result}

        self.assertIn(unseen.id, ids)
        self.assertNotIn(seen.id, ids)

    def test_get_pending_offers_with_listing_by_sender_filters_pending(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing1 = self._create_listing(seller.id)
        listing2 = self._create_listing(seller.id)

        pending = self._create_offer(listing1.id, buyer.id)
        rejected = self._create_offer(listing2.id, buyer.id)
        self._offer_db.set_accepted(rejected.id, False)

        result = self._mgr.get_pending_offers_with_listing_by_sender(buyer.id)
        ids = {o.id for o in result}

        self.assertIn(pending.id, ids)
        self.assertNotIn(rejected.id, ids)

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    def test_set_offer_seen_marks_offer_seen(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)
        offer = self._create_offer(listing.id, buyer.id)

        self._mgr.set_offer_seen(offer.id)

        fetched = self._offer_db.get_by_id(offer.id)
        self.assertTrue(bool(fetched.seen))

    def test_set_offer_accepted_accepts_and_rejects_others(self) -> None:
        seller = self._create_account("seller")
        buyer1 = self._create_account("buyer1")
        buyer2 = self._create_account("buyer2")
        listing = self._create_listing(seller.id)

        accepted_offer = self._create_offer(listing.id, buyer1.id)
        other_offer = self._create_offer(listing.id, buyer2.id)

        self._mgr.set_offer_accepted(accepted_offer.id, True, seller.id)

        accepted_fetched = self._offer_db.get_by_id(accepted_offer.id)
        other_fetched = self._offer_db.get_by_id(other_offer.id)

        self.assertTrue(bool(accepted_fetched.accepted))
        self.assertFalse(bool(other_fetched.accepted))

    def test_set_offer_accepted_declines_offer(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)
        offer = self._create_offer(listing.id, buyer.id)

        self._mgr.set_offer_accepted(offer.id, False, seller.id)

        fetched = self._offer_db.get_by_id(offer.id)
        self.assertFalse(bool(fetched.accepted))

    def test_set_offer_accepted_raises_when_not_seller(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        intruder = self._create_account("intruder")
        listing = self._create_listing(seller.id)
        offer = self._create_offer(listing.id, buyer.id)

        with self.assertRaises(UnapprovedBehaviorError):
            self._mgr.set_offer_accepted(offer.id, True, intruder.id)

    def test_set_offer_accepted_raises_when_offer_not_found(self) -> None:
        with self.assertRaises(OfferNotFoundError):
            self._mgr.set_offer_accepted(999999999, True, 1)

    def test_set_offer_accepted_raises_when_already_resolved(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)
        offer = self._create_offer(listing.id, buyer.id)

        self._mgr.set_offer_accepted(offer.id, False, seller.id)

        with self.assertRaises(UnapprovedBehaviorError):
            self._mgr.set_offer_accepted(offer.id, True, seller.id)

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------

    def test_delete_offer_removes_offer(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)
        offer = self._create_offer(listing.id, buyer.id)

        result = self._mgr.delete_offer(offer.id)

        self.assertTrue(result)
        self.assertIsNone(self._offer_db.get_by_id(offer.id))

    def test_delete_offer_returns_false_when_not_found(self) -> None:
        result = self._mgr.delete_offer(999999999)
        self.assertFalse(result)
