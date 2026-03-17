from __future__ import annotations

import unittest
from uuid import uuid4

from src.business_logic.managers.account.account_manager import AccountManager
from src.business_logic.managers.listing.listing_manager import ListingManager
from src.business_logic.managers.offer.offer_manager import OfferManager
from src.business_logic.services.offer_service import OfferService
from src.db.account.mysql import MySQLAccountDB
from src.db.comment.mysql import MySQLCommentDB
from src.db.listing.mysql.mysql_listing_db import MySQLListingDB
from src.db.offer.mysql.mysql_offer_db import MySQLOfferDB
from src.domain_models.account import Account
from src.domain_models.listing import Listing
from src.domain_models.offer import Offer
from src.utils import ConflictError, ListingNotFoundError, OfferNotFoundError, UnapprovedBehaviorError

from tests.helpers.integration_db import ensure_tables_exist, reset_all_tables
from tests.helpers.integration_db_session import acquire, get_db, release


class TestOfferServiceIntegration(unittest.TestCase):
    """
    Integration tests:
      OfferService -> OfferManager + ListingManager + AccountManager
                   -> MySQL* DBs -> real MySQL (docker)
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls._session = acquire(timeout_s=60)
        cls._db = get_db()

        cls._account_db = MySQLAccountDB(cls._db)
        cls._listing_db = MySQLListingDB(cls._db)
        cls._comment_db = MySQLCommentDB(cls._db)
        cls._offer_db = MySQLOfferDB(cls._db)

        cls._account_mgr = AccountManager(cls._account_db, listing_db=cls._listing_db)
        cls._listing_mgr = ListingManager(cls._listing_db, cls._comment_db)
        cls._offer_mgr = OfferManager(cls._offer_db, cls._listing_db)

        cls._service = OfferService(
            offer_manager=cls._offer_mgr,
            listing_manager=cls._listing_mgr,
            account_manager=cls._account_mgr,
        )

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

    def _create_offer(self, listing_id: int, sender_id: int, price: float = 90.0) -> Offer:
        offer = self._service.create_offer(Offer(
            listing_id=listing_id,
            sender_id=sender_id,
            offered_price=price,
        ))
        self.assertIsNotNone(offer.id)
        return offer

    # --------------------------------------------------
    # create_offer
    # --------------------------------------------------

    def test_create_offer_persists_and_returns_id(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)

        offer = self._service.create_offer(Offer(
            listing_id=listing.id,
            sender_id=buyer.id,
            offered_price=75.0,
        ))

        self.assertIsNotNone(offer.id)
        fetched = self._offer_db.get_by_id(offer.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.sender_id, buyer.id)

    def test_create_offer_raises_when_listing_not_found(self) -> None:
        buyer = self._create_account("buyer")

        with self.assertRaises(ListingNotFoundError):
            self._service.create_offer(Offer(
                listing_id=999999999,
                sender_id=buyer.id,
                offered_price=80.0,
            ))

    def test_create_offer_raises_when_sender_is_seller(self) -> None:
        seller = self._create_account("seller")
        listing = self._create_listing(seller.id)

        with self.assertRaises(UnapprovedBehaviorError):
            self._service.create_offer(Offer(
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
            self._service.create_offer(Offer(
                listing_id=listing.id,
                sender_id=buyer.id,
                offered_price=95.0,
            ))

    # --------------------------------------------------
    # resolve_offer — accept
    # --------------------------------------------------

    def test_resolve_offer_accept_marks_listing_sold(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)
        offer = self._create_offer(listing.id, buyer.id)

        self._service.resolve_offer(offer_id=offer.id, accepted=True, actor_id=seller.id)

        listing_fetched = self._listing_db.get_by_id(listing.id)
        self.assertTrue(bool(listing_fetched.is_sold))
        self.assertEqual(listing_fetched.sold_to_id, buyer.id)

    def test_resolve_offer_accept_rejects_all_other_pending_offers(self) -> None:
        seller = self._create_account("seller")
        buyer1 = self._create_account("buyer1")
        buyer2 = self._create_account("buyer2")
        buyer3 = self._create_account("buyer3")
        listing = self._create_listing(seller.id)

        accepted_offer = self._create_offer(listing.id, buyer1.id)
        other1 = self._create_offer(listing.id, buyer2.id)
        other2 = self._create_offer(listing.id, buyer3.id)

        self._service.resolve_offer(offer_id=accepted_offer.id, accepted=True, actor_id=seller.id)

        self.assertTrue(bool(self._offer_db.get_by_id(accepted_offer.id).accepted))
        self.assertFalse(bool(self._offer_db.get_by_id(other1.id).accepted))
        self.assertFalse(bool(self._offer_db.get_by_id(other2.id).accepted))

    def test_resolve_offer_accept_raises_when_not_seller(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        intruder = self._create_account("intruder")
        listing = self._create_listing(seller.id)
        offer = self._create_offer(listing.id, buyer.id)

        with self.assertRaises(UnapprovedBehaviorError):
            self._service.resolve_offer(offer_id=offer.id, accepted=True, actor_id=intruder.id)

        listing_fetched = self._listing_db.get_by_id(listing.id)
        self.assertFalse(bool(listing_fetched.is_sold))

    # --------------------------------------------------
    # resolve_offer — decline
    # --------------------------------------------------

    def test_resolve_offer_decline_does_not_mark_listing_sold(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)
        offer = self._create_offer(listing.id, buyer.id)

        self._service.resolve_offer(offer_id=offer.id, accepted=False, actor_id=seller.id)

        offer_fetched = self._offer_db.get_by_id(offer.id)
        self.assertFalse(bool(offer_fetched.accepted))

        listing_fetched = self._listing_db.get_by_id(listing.id)
        self.assertFalse(bool(listing_fetched.is_sold))

    # --------------------------------------------------
    # resolve_offer — error paths
    # --------------------------------------------------

    def test_resolve_offer_raises_offer_not_found(self) -> None:
        with self.assertRaises(OfferNotFoundError):
            self._service.resolve_offer(offer_id=999999999, accepted=True, actor_id=1)

    def test_resolve_offer_raises_when_already_resolved(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)
        offer = self._create_offer(listing.id, buyer.id)

        self._service.resolve_offer(offer_id=offer.id, accepted=False, actor_id=seller.id)

        with self.assertRaises(UnapprovedBehaviorError):
            self._service.resolve_offer(offer_id=offer.id, accepted=True, actor_id=seller.id)

    # --------------------------------------------------
    # Aggregated reads (end-to-end)
    # --------------------------------------------------

    def test_get_offers_sellers_returns_all_offers_across_listings(self) -> None:
        seller = self._create_account("seller")
        buyer1 = self._create_account("buyer1")
        buyer2 = self._create_account("buyer2")
        listing1 = self._create_listing(seller.id)
        listing2 = self._create_listing(seller.id)

        o1 = self._create_offer(listing1.id, buyer1.id)
        o2 = self._create_offer(listing2.id, buyer2.id)

        result = self._service.get_offers_sellers(seller.id)
        ids = {o.id for o in result}

        self.assertIn(o1.id, ids)
        self.assertIn(o2.id, ids)

    def test_get_offer_sellers_pending_excludes_resolved(self) -> None:
        seller = self._create_account("seller")
        buyer1 = self._create_account("buyer1")
        buyer2 = self._create_account("buyer2")
        listing = self._create_listing(seller.id)

        pending = self._create_offer(listing.id, buyer1.id)
        declined = self._create_offer(listing.id, buyer2.id)
        self._offer_db.set_accepted(declined.id, False)

        result = self._service.get_offer_sellers_pending(seller.id)
        ids = {o.id for o in result}

        self.assertIn(pending.id, ids)
        self.assertNotIn(declined.id, ids)

    def test_get_offer_sellers_unseen_excludes_seen(self) -> None:
        seller = self._create_account("seller")
        buyer1 = self._create_account("buyer1")
        buyer2 = self._create_account("buyer2")
        listing = self._create_listing(seller.id)

        unseen = self._create_offer(listing.id, buyer1.id)
        seen = self._create_offer(listing.id, buyer2.id)
        self._offer_db.set_seen(seen.id)

        result = self._service.get_offer_sellers_unseen(seller.id)
        ids = {o.id for o in result}

        self.assertIn(unseen.id, ids)
        self.assertNotIn(seen.id, ids)

    def test_get_pending_offers_with_listing_by_sender(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing1 = self._create_listing(seller.id)
        listing2 = self._create_listing(seller.id)

        pending = self._create_offer(listing1.id, buyer.id)
        declined = self._create_offer(listing2.id, buyer.id)
        self._offer_db.set_accepted(declined.id, False)

        result = self._service.get_pending_offers_with_listing_by_sender(buyer.id)
        ids = {o.id for o in result}

        self.assertIn(pending.id, ids)
        self.assertNotIn(declined.id, ids)

    # --------------------------------------------------
    # set_offer_seen
    # --------------------------------------------------

    def test_set_offer_seen_marks_offer_seen(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)
        offer = self._create_offer(listing.id, buyer.id)

        self._service.set_offer_seen(offer.id)

        fetched = self._offer_db.get_by_id(offer.id)
        self.assertTrue(bool(fetched.seen))

    # --------------------------------------------------
    # delete_offer
    # --------------------------------------------------

    def test_delete_offer_removes_offer(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")
        listing = self._create_listing(seller.id)
        offer = self._create_offer(listing.id, buyer.id)

        result = self._service.delete_offer(offer.id)

        self.assertTrue(result)
        self.assertIsNone(self._offer_db.get_by_id(offer.id))
