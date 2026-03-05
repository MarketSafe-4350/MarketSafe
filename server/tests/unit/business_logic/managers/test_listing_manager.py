from __future__ import annotations

import unittest
from unittest.mock import Mock, MagicMock

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
        self.comment_db.get_by_listing_id.return_value = (
            []
        )  # can be fake Comment objects later

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

    def test_list_unsold_listings_delegates(self):
        expected = []
        self.listing_db.get_unsold.return_value = expected

        result = self.mgr.list_unsold_listings()

        self.listing_db.get_unsold.assert_called_once_with()
        self.assertIs(result, expected)

    # ---- list_recent_unsold ----
    def test_list_recent_unsold_defaults_delegates(self):
        expected = []
        self.listing_db.get_recent_unsold.return_value = expected

        result = self.mgr.list_recent_unsold()

        self.listing_db.get_recent_unsold.assert_called_once_with(limit=50, offset=0)
        self.assertIs(result, expected)

    def test_list_recent_unsold_invalid_limit_raises(self):
        with self.assertRaises(Exception):
            self.mgr.list_recent_unsold(limit="bad")  # type: ignore[arg-type]

    def test_list_recent_unsold_invalid_offset_raises(self):
        with self.assertRaises(Exception):
            self.mgr.list_recent_unsold(offset="bad")  # type: ignore[arg-type]

    # ---- list_unsold_by_location ----
    def test_list_unsold_by_location_delegates(self):
        expected = []
        self.listing_db.get_unsold_by_location.return_value = expected

        result = self.mgr.list_unsold_by_location("Winnipeg")

        self.listing_db.get_unsold_by_location.assert_called_once_with("Winnipeg")
        self.assertIs(result, expected)

    def test_list_unsold_by_location_invalid_raises(self):
        with self.assertRaises(Exception):
            self.mgr.list_unsold_by_location(None)  # type: ignore[arg-type]

    # ---- list_unsold_by_max_price ----
    def test_list_unsold_by_max_price_delegates(self):
        expected = []
        self.listing_db.get_unsold_by_max_price.return_value = expected

        result = self.mgr.list_unsold_by_max_price(100.0)

        self.listing_db.get_unsold_by_max_price.assert_called_once_with(100.0)
        self.assertIs(result, expected)

    def test_list_unsold_by_max_price_invalid_raises(self):
        with self.assertRaises(Exception):
            self.mgr.list_unsold_by_max_price(-1)

    # ---- list_unsold_by_location_and_max_price ----
    def test_list_unsold_by_location_and_max_price_delegates(self):
        expected = []
        self.listing_db.get_unsold_by_location_and_max_price.return_value = expected

        result = self.mgr.list_unsold_by_location_and_max_price("Winnipeg", 50.0)

        self.listing_db.get_unsold_by_location_and_max_price.assert_called_once_with(
            "Winnipeg", 50.0
        )
        self.assertIs(result, expected)

    def test_list_unsold_by_location_and_max_price_invalid_location_raises(self):
        with self.assertRaises(Exception):
            self.mgr.list_unsold_by_location_and_max_price(None, 50.0)  # type: ignore[arg-type]

    def test_list_unsold_by_location_and_max_price_invalid_price_raises(self):
        with self.assertRaises(Exception):
            self.mgr.list_unsold_by_location_and_max_price("Winnipeg", -1)

    # ---- find_unsold_by_title_keyword ----
    def test_find_unsold_by_title_keyword_defaults_delegates(self):
        expected = []
        self.listing_db.find_unsold_by_title_keyword.return_value = expected

        result = self.mgr.find_unsold_by_title_keyword("desk")

        self.listing_db.find_unsold_by_title_keyword.assert_called_once_with(
            "desk", limit=50, offset=0
        )
        self.assertIs(result, expected)

    def test_find_unsold_by_title_keyword_invalid_keyword_raises(self):
        with self.assertRaises(Exception):
            self.mgr.find_unsold_by_title_keyword(None)  # type: ignore[arg-type]

    def test_find_unsold_by_title_keyword_invalid_limit_raises(self):
        with self.assertRaises(Exception):
            self.mgr.find_unsold_by_title_keyword("desk", limit="bad")  # type: ignore[arg-type]

    def test_find_unsold_by_title_keyword_invalid_offset_raises(self):
        with self.assertRaises(Exception):
            self.mgr.find_unsold_by_title_keyword("desk", offset="bad")  # type: ignore[arg-type]

    # ---- list_listings_by_seller ----
    def test_list_listings_by_seller_delegates(self):
        expected = []
        self.listing_db.get_by_seller_id.return_value = expected

        result = self.mgr.list_listings_by_seller(123)

        self.listing_db.get_by_seller_id.assert_called_once_with(123)
        self.assertIs(result, expected)

    def test_list_listings_by_seller_invalid_raises(self):
        with self.assertRaises(Exception):
            self.mgr.list_listings_by_seller("bad")  # type: ignore[arg-type]

    # ---- list_listings_by_buyer ----
    def test_list_listings_by_buyer_delegates(self):
        expected = []
        self.listing_db.get_by_buyer_id.return_value = expected

        result = self.mgr.list_listings_by_buyer(456)

        self.listing_db.get_by_buyer_id.assert_called_once_with(456)
        self.assertIs(result, expected)

    def test_list_listings_by_buyer_invalid_raises(self):
        with self.assertRaises(Exception):
            self.mgr.list_listings_by_buyer("bad")  # type: ignore[arg-type]

    def test_update_listing_delegates_to_db_update(self):
        listing = MagicMock(spec=Listing)
        listing.id = 123

        self.listing_db.update.return_value = listing

        result = self.mgr.update_listing(listing)

        self.listing_db.update.assert_called_once_with(listing)
        self.assertIs(result, listing)

    def test_update_listing_none_raises(self):
        with self.assertRaises(Exception):
            self.mgr.update_listing(None)

    def test_update_listing_missing_id_raises(self):
        listing = MagicMock(spec=Listing)
        listing.id = None

        with self.assertRaises(Exception):
            self.mgr.update_listing(listing)

    # -----------------------------
    # update_listing_price
    # -----------------------------
    def test_update_listing_price_delegates_to_set_price(self):
        self.mgr.update_listing_price(10, 25.0)

        self.listing_db.set_price.assert_called_once_with(10, 25.0)

    def test_update_listing_price_invalid_listing_id_raises(self):
        with self.assertRaises(Exception):
            self.mgr.update_listing_price("bad", 25.0)

    def test_update_listing_price_invalid_price_raises(self):
        with self.assertRaises(Exception):
            self.mgr.update_listing_price(10, -1)

    # -----------------------------
    # delete_listing
    # -----------------------------
    def test_delete_listing_delegates_to_remove_and_returns_value(self):
        self.listing_db.remove.return_value = True

        result = self.mgr.delete_listing(999)

        self.listing_db.remove.assert_called_once_with(999)
        self.assertTrue(result)

    def test_delete_listing_invalid_id_raises(self):
        with self.assertRaises(Exception):
            self.mgr.delete_listing("bad")

        # -----------------------------

    # create_listing
    # -----------------------------
    def test_create_listing_delegates_to_db_add(self) -> None:
        listing = self._listing(listing_id=None, seller_id=1)
        self.listing_db.add.return_value = listing

        out = self.mgr.create_listing(listing)

        self.assertIs(out, listing)
        self.listing_db.add.assert_called_once_with(listing)

    def test_create_listing_none_raises(self) -> None:
        with self.assertRaises(Exception):
            self.mgr.create_listing(None)

    # -----------------------------
    # get_listing_by_id
    # -----------------------------
    def test_get_listing_by_id_delegates(self) -> None:
        self.listing_db.get_by_id.return_value = None

        out = self.mgr.get_listing_by_id(10)

        self.assertIsNone(out)
        self.listing_db.get_by_id.assert_called_once_with(10)

    def test_get_listing_by_id_invalid_raises(self) -> None:
        with self.assertRaises(Exception):
            self.mgr.get_listing_by_id("bad")

    # -----------------------------
    # list_listings
    # -----------------------------
    def test_list_listings_delegates(self) -> None:
        expected = []
        self.listing_db.get_all.return_value = expected

        out = self.mgr.list_listings()

        self.assertIs(out, expected)
        self.listing_db.get_all.assert_called_once_with()

    # -----------------------------
    # get_listing_with_comments
    # -----------------------------
    def test_get_listing_with_comments_returns_none_when_missing_fixed(self) -> None:
        self.listing_db.get_by_id.return_value = None

        out = self.mgr.get_listing_with_comments(123)

        self.assertIsNone(out)
        self.listing_db.get_by_id.assert_called_once_with(123)
        self.comment_db.get_by_listing_id.assert_not_called()

    # -----------------------------
    # mark_listing_sold: null checks
    # -----------------------------
    def test_mark_listing_sold_actor_none_raises(self) -> None:
        buyer = self._account(2)
        listing = self._listing(listing_id=5, seller_id=1)

        with self.assertRaises(Exception):
            self.mgr.mark_listing_sold(actor=None, listing=listing, buyer=buyer)

        self.listing_db.set_sold.assert_not_called()

    def test_mark_listing_sold_listing_none_raises(self) -> None:
        actor = self._account(1)
        buyer = self._account(2)

        with self.assertRaises(Exception):
            self.mgr.mark_listing_sold(actor=actor, listing=None, buyer=buyer)

        self.listing_db.set_sold.assert_not_called()

    def test_mark_listing_sold_buyer_none_raises(self) -> None:
        actor = self._account(1)
        listing = self._listing(listing_id=5, seller_id=1)

        with self.assertRaises(Exception):
            self.mgr.mark_listing_sold(actor=actor, listing=listing, buyer=None)

        self.listing_db.set_sold.assert_not_called()

    def test_mark_listing_sold_buyer_id_none_raises(self) -> None:
        actor = self._account(1)
        buyer = MagicMock(spec=Account)
        buyer.id = None  # forces Validation.require_int to raise
        listing = self._listing(listing_id=5, seller_id=actor.id)

        with self.assertRaises(Exception):
            self.mgr.mark_listing_sold(actor=actor, listing=listing, buyer=buyer)

        self.listing_db.set_sold.assert_not_called()
