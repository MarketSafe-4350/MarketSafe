from __future__ import annotations

import unittest
from unittest.mock import Mock

from src.business_logic.managers.listing.listing_manager import ListingManager
from src.domain_models import Account, Listing, Comment
from src.utils import ListingNotFoundError, UnapprovedBehaviorError


class TestListingManagerUnit(unittest.TestCase):
    def setUp(self) -> None:
        self.listing_db = Mock()
        self.comment_db = Mock()
        self.mgr = ListingManager(self.listing_db, self.comment_db)

    def _account(self, account_id: int) -> Account:
        return Account(
            email=f"user{account_id}@example.com",
            password="pass",
            fname="A",
            lname="B",
            verified=False,
            account_id=account_id,
        )

    def _listing(
            self,
            *,
            listing_id: int | None,
            seller_id: int,
            is_sold: bool = False,
            sold_to_id: int | None = None,
    ) -> Listing:
        if is_sold and sold_to_id is None:
            sold_to_id = 999  # any positive int that is not the seller, for unit tests

        if (not is_sold) and sold_to_id is not None:
            sold_to_id = None

        return Listing(
            seller_id=seller_id,
            title="t",
            description="d",
            price=10.0,
            listing_id=listing_id,
            is_sold=is_sold,
            sold_to_id=sold_to_id,
            location="Winnipeg",
        )
        
    def _comment(
        self,
        *,
        comment_id: int | None,
        listing_id: int,
        author_id: int,
        body: str | None = "none",
    ) -> Comment:
        return Comment(
            listing_id=listing_id,
            author_id=author_id,
            body=body,
            comment_id=comment_id,
        )
    # -----------------------------
    # orchestration
    # -----------------------------
    def test_get_listing_with_comments_returns_none_when_missing(self) -> None:
        self.listing_db.get_by_id.return_value = None

        out = self.mgr.get_listing_with_comments(123)

        self.assertIsNone(out)
        self.listing_db.get_by_id.assert_called_once_with(123)
        self.comment_db.get_for_listing.assert_not_called()

    def test_get_listing_with_comments_attaches_comments(self) -> None:
        listing = self._listing(listing_id=10, seller_id=1)
        self.listing_db.get_by_id.return_value = listing
        self.comment_db.get_by_listing_id.return_value = []  # can be fake Comment objects later

        out = self.mgr.get_listing_with_comments(10)

        self.assertIsNotNone(out)
        assert out is not None
        self.comment_db.get_by_listing_id.assert_called_once_with(10)
        self.assertEqual(out.comments, [])

    # -----------------------------
    # authorization + selling
    # -----------------------------
    def test_mark_listing_sold_requires_persisted_listing(self) -> None:
        actor = self._account(1)
        buyer = self._account(2)
        listing = self._listing(listing_id=None, seller_id=1)

        with self.assertRaises(ListingNotFoundError):
            self.mgr.mark_listing_sold(actor=actor, listing=listing, buyer=buyer)

        self.listing_db.set_sold.assert_not_called()

    def test_mark_listing_sold_only_seller_can_mark_sold(self) -> None:
        seller = self._account(1)
        actor = self._account(99)
        buyer = self._account(2)
        listing = self._listing(listing_id=5, seller_id=seller.id)

        with self.assertRaises(UnapprovedBehaviorError):
            self.mgr.mark_listing_sold(actor=actor, listing=listing, buyer=buyer)

        self.listing_db.set_sold.assert_not_called()

    def test_mark_listing_sold_seller_cannot_buy_own_listing(self) -> None:
        seller = self._account(1)
        listing = self._listing(listing_id=5, seller_id=seller.id)

        with self.assertRaises(UnapprovedBehaviorError):
            self.mgr.mark_listing_sold(actor=seller, listing=listing, buyer=seller)

        self.listing_db.set_sold.assert_not_called()

    def test_mark_listing_sold_cannot_double_sell(self) -> None:
        seller = self._account(1)
        buyer = self._account(2)
        listing = self._listing(listing_id=5, seller_id=seller.id, is_sold=True)

        with self.assertRaises(UnapprovedBehaviorError):
            self.mgr.mark_listing_sold(actor=seller, listing=listing, buyer=buyer)

        self.listing_db.set_sold.assert_not_called()

    def test_mark_listing_sold_happy_path_calls_db(self) -> None:
        seller = self._account(1)
        buyer = self._account(2)
        listing = self._listing(listing_id=5, seller_id=seller.id, is_sold=False)

        self.mgr.mark_listing_sold(actor=seller, listing=listing, buyer=buyer)

        self.listing_db.set_sold.assert_called_once_with(
            listing_id=5,
            is_sold=True,
            sold_to_id=buyer.id,
        )