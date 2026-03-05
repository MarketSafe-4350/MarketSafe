from __future__ import annotations

import unittest
from uuid import uuid4
from typing import List

from src.business_logic.managers.listing.abstract_listing_manager import CommentDB
from src.business_logic.managers.listing.listing_manager import ListingManager
from src.db.account.mysql import MySQLAccountDB
from src.db.listing.mysql.mysql_listing_db import MySQLListingDB
from src.db.comment.mysql import MySQLCommentDB
from src.domain_models import Account, Listing
from src.domain_models import Comment
from src.utils import ListingNotFoundError, UnapprovedBehaviorError

from tests.helpers.integration_db import ensure_tables_exist, reset_all_tables
from tests.helpers.integration_db_session import acquire, get_db, release


class TestListingManagerIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._session = acquire(timeout_s=60)
        cls._db = get_db()

        cls._account_db = MySQLAccountDB(cls._db)
        cls._listing_db = MySQLListingDB(cls._db)
        cls._comment_db = MySQLCommentDB(cls._db)

        cls._mgr = ListingManager(cls._listing_db, cls._comment_db)

        ensure_tables_exist(cls._db, timeout_s=60)
        reset_all_tables(cls._db)

    @classmethod
    def tearDownClass(cls) -> None:
        release(cls._session, remove_volumes=False)

    def setUp(self) -> None:
        # Keep tests independent
        reset_all_tables(self._db)

    # -----------------------------
    # helpers
    # -----------------------------
    def _new_account(self, prefix: str = "user") -> Account:
        uniq = uuid4().hex[:10]
        return Account(
            email=f"{prefix}_{uniq}@example.com",
            password="pass",
            fname="Test",
            lname="User",
            verified=False,
        )

    def _create_account(self, prefix: str = "user") -> Account:
        created = self._account_db.add(self._new_account(prefix))
        self.assertIsNotNone(created.id)
        return created

    def _new_listing(
        self, seller_id: int, *, title: str | None = None, price: float = 123.45
    ) -> Listing:
        uniq = uuid4().hex[:10]
        # IMPORTANT: create UNSOLD listing (valid domain state)
        return Listing(
            seller_id=seller_id,
            title=title or f"Title {uniq}",
            description=f"Desc {uniq}",
            price=price,
            location="Winnipeg",
            is_sold=False,
            sold_to_id=None,
        )

    # -----------------------------
    # tests
    # -----------------------------
    def test_create_and_get_listing(self) -> None:
        seller = self._create_account("seller")
        created = self._mgr.create_listing(self._new_listing(seller.id))

        self.assertIsNotNone(created.id)

        fetched = self._mgr.get_listing_by_id(created.id)
        self.assertIsNotNone(fetched)

    def test_get_listing_with_comments_attaches_empty_comments(self) -> None:
        seller = self._create_account("seller")
        created = self._mgr.create_listing(self._new_listing(seller.id))

        listing = self._mgr.get_listing_with_comments(created.id)
        self.assertIsNotNone(listing)
        assert listing is not None
        self.assertEqual(listing.comments, [])

    def test_mark_listing_sold_authorized(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")

        created = self._mgr.create_listing(self._new_listing(seller.id))

        self._mgr.mark_listing_sold(actor=seller, listing=created, buyer=buyer)

        refreshed = self._mgr.get_listing_by_id(created.id)
        self.assertIsNotNone(refreshed)
        assert refreshed is not None

        self.assertTrue(bool(refreshed.is_sold))
        self.assertEqual(refreshed.sold_to_id, buyer.id)

    def test_mark_listing_sold_unauthorized_actor_raises(self) -> None:
        seller = self._create_account("seller")
        actor = self._create_account("not_seller")
        buyer = self._create_account("buyer")

        created = self._mgr.create_listing(self._new_listing(seller.id))

        with self.assertRaises(UnapprovedBehaviorError):
            self._mgr.mark_listing_sold(actor=actor, listing=created, buyer=buyer)

    def test_mark_listing_sold_requires_persisted_listing(self) -> None:
        seller = self._create_account("seller")
        buyer = self._create_account("buyer")

        not_persisted = self._new_listing(seller.id)  # id=None

        with self.assertRaises(ListingNotFoundError):
            self._mgr.mark_listing_sold(
                actor=seller, listing=not_persisted, buyer=buyer
            )

    def test_mark_listing_sold_seller_cannot_buy_own_listing(self) -> None:
        seller = self._create_account("seller")
        created = self._mgr.create_listing(self._new_listing(seller.id))

        with self.assertRaises(UnapprovedBehaviorError):
            self._mgr.mark_listing_sold(actor=seller, listing=created, buyer=seller)

    def test_mark_listing_sold_cannot_double_sell(self) -> None:
        """
        Avoid the domain invariant error by not constructing sold Listing directly.
        We first sell it properly, then re-fetch it (sold_to_id will be populated),
        then attempt selling again.
        """
        seller = self._create_account("seller")
        buyer1 = self._create_account("buyer1")
        buyer2 = self._create_account("buyer2")

        created = self._mgr.create_listing(self._new_listing(seller.id))

        # First sale is valid
        self._mgr.mark_listing_sold(actor=seller, listing=created, buyer=buyer1)

        # Re-fetch (ensures we have a valid sold Listing object: is_sold=True AND sold_to_id set)
        sold_listing = self._mgr.get_listing_by_id(created.id)
        self.assertIsNotNone(sold_listing)
        assert sold_listing is not None
        self.assertTrue(bool(sold_listing.is_sold))
        self.assertIsNotNone(sold_listing.sold_to_id)

        # Second sale should fail
        with self.assertRaises(UnapprovedBehaviorError):
            self._mgr.mark_listing_sold(
                actor=seller, listing=sold_listing, buyer=buyer2
            )
