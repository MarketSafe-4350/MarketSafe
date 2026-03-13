from __future__ import annotations

import unittest
from unittest.mock import Mock

from src.business_logic.managers.listing.listing_manager import ListingManager
from src.domain_models import Listing, Rating, Comment
from src.utils import ConfigurationError


class TestListingManagerRatingPathsUnit(unittest.TestCase):
    def setUp(self) -> None:
        self.listing_db = Mock()
        self.comment_db = Mock()
        self.rating_db = Mock()
        self.mgr = ListingManager(self.listing_db, self.comment_db, self.rating_db)
        self.mgr_no_rating = ListingManager(self.listing_db, self.comment_db, None)

    def _listing(
        self,
        *,
        listing_id: int | None,
        seller_id: int = 1,
        is_sold: bool = False,
        sold_to_id: int | None = None,
    ) -> Listing:
        if is_sold and sold_to_id is None:
            sold_to_id = 2

        return Listing(
            seller_id=seller_id,
            title="title",
            description="desc",
            price=10.0,
            listing_id=listing_id,
            is_sold=is_sold,
            sold_to_id=sold_to_id,
            location="Winnipeg",
            comments=[],
        )

    def _rating(self, *, listing_id: int, rater_id: int = 2, score: int = 5) -> Rating:
        return Rating(
            listing_id=listing_id,
            rater_id=rater_id,
            transaction_rating=score,
        )

    def _comment(self, *, listing_id: int, author_id: int = 3, body: str = "hello") -> Comment:
        return Comment(
            listing_id=listing_id,
            author_id=author_id,
            body=body,
        )

    # -----------------------------
    # fill_listing_rating_value
    # -----------------------------
    def test_fill_listing_rating_value_raises_when_rating_db_missing(self) -> None:
        listing = self._listing(listing_id=10, is_sold=True, sold_to_id=2)

        with self.assertRaises(ConfigurationError):
            self.mgr_no_rating.fill_listing_rating_value(listing)

    def test_fill_listing_rating_value_returns_same_listing_when_listing_id_none(self) -> None:
        listing = self._listing(listing_id=None, is_sold=True, sold_to_id=2)

        out = self.mgr.fill_listing_rating_value(listing)

        self.assertIs(out, listing)
        self.assertIsNone(out.rating)
        self.rating_db.get_by_listing_id.assert_not_called()

    def test_fill_listing_rating_value_populates_rating_when_available(self) -> None:
        listing = self._listing(listing_id=10, is_sold=True, sold_to_id=2)
        rating = self._rating(listing_id=10)
        self.rating_db.get_by_listing_id.return_value = rating

        out = self.mgr.fill_listing_rating_value(listing)

        self.assertIs(out, listing)
        self.assertIs(out.rating, rating)
        self.rating_db.get_by_listing_id.assert_called_once_with(10)

    def test_fill_listing_rating_value_sets_none_when_rating_missing(self) -> None:
        listing = self._listing(listing_id=10, is_sold=True, sold_to_id=2)
        self.rating_db.get_by_listing_id.return_value = None

        out = self.mgr.fill_listing_rating_value(listing)

        self.assertIs(out, listing)
        self.assertIsNone(out.rating)
        self.rating_db.get_by_listing_id.assert_called_once_with(10)

    # -----------------------------
    # get_listing_with_rating_by_id
    # -----------------------------
    def test_get_listing_with_rating_by_id_raises_when_rating_db_missing(self) -> None:
        with self.assertRaises(ConfigurationError):
            self.mgr_no_rating.get_listing_with_rating_by_id(10)

    def test_get_listing_with_rating_by_id_returns_none_when_listing_missing(self) -> None:
        self.listing_db.get_by_id.return_value = None

        out = self.mgr.get_listing_with_rating_by_id(10)

        self.assertIsNone(out)
        self.listing_db.get_by_id.assert_called_once_with(10)
        self.rating_db.get_by_listing_id.assert_not_called()

    def test_get_listing_with_rating_by_id_returns_listing_with_rating(self) -> None:
        listing = self._listing(listing_id=10, is_sold=True, sold_to_id=2)
        rating = self._rating(listing_id=10)
        self.listing_db.get_by_id.return_value = listing
        self.rating_db.get_by_listing_id.return_value = rating

        out = self.mgr.get_listing_with_rating_by_id(10)

        self.assertIs(out, listing)
        self.assertIs(out.rating, rating)
        self.listing_db.get_by_id.assert_called_once_with(10)
        self.rating_db.get_by_listing_id.assert_called_once_with(10)

    # -----------------------------
    # get_listing_with_comments_and_rating
    # -----------------------------
    def test_get_listing_with_comments_and_rating_raises_when_rating_db_missing(self) -> None:
        with self.assertRaises(ConfigurationError):
            self.mgr_no_rating.get_listing_with_comments_and_rating(10)

    def test_get_listing_with_comments_and_rating_returns_none_when_listing_missing(self) -> None:
        self.listing_db.get_by_id.return_value = None

        out = self.mgr.get_listing_with_comments_and_rating(10)

        self.assertIsNone(out)
        self.listing_db.get_by_id.assert_called_once_with(10)
        self.comment_db.get_by_listing_id.assert_not_called()
        self.rating_db.get_by_listing_id.assert_not_called()

    def test_get_listing_with_comments_and_rating_populates_both(self) -> None:
        listing = self._listing(listing_id=10, is_sold=True, sold_to_id=2)
        comments = [self._comment(listing_id=10)]
        rating = self._rating(listing_id=10)

        self.listing_db.get_by_id.return_value = listing
        self.comment_db.get_by_listing_id.return_value = comments
        self.rating_db.get_by_listing_id.return_value = rating

        out = self.mgr.get_listing_with_comments_and_rating(10)

        self.assertIs(out, listing)
        self.assertEqual(out.comments, comments)
        self.assertIs(out.rating, rating)
        self.listing_db.get_by_id.assert_called_once_with(10)
        self.comment_db.get_by_listing_id.assert_called_once_with(10)
        self.rating_db.get_by_listing_id.assert_called_once_with(10)

    # -----------------------------
    # create_listing / get_listing_by_id / update_listing
    # with rating db configured
    # -----------------------------
    def test_create_listing_populates_rating_when_rating_db_available(self) -> None:
        listing = self._listing(listing_id=10, is_sold=True, sold_to_id=2)
        rating = self._rating(listing_id=10)

        self.listing_db.add.return_value = listing
        self.rating_db.get_by_listing_id.return_value = rating

        out = self.mgr.create_listing(listing)

        self.assertIs(out, listing)
        self.assertIs(out.rating, rating)
        self.listing_db.add.assert_called_once_with(listing)
        self.rating_db.get_by_listing_id.assert_called_once_with(10)

    def test_get_listing_by_id_populates_rating_when_rating_db_available(self) -> None:
        listing = self._listing(listing_id=10, is_sold=True, sold_to_id=2)
        rating = self._rating(listing_id=10)

        self.listing_db.get_by_id.return_value = listing
        self.rating_db.get_by_listing_id.return_value = rating

        out = self.mgr.get_listing_by_id(10)

        self.assertIs(out, listing)
        self.assertIs(out.rating, rating)
        self.listing_db.get_by_id.assert_called_once_with(10)
        self.rating_db.get_by_listing_id.assert_called_once_with(10)

    def test_update_listing_populates_rating_when_rating_db_available(self) -> None:
        listing = self._listing(listing_id=10, is_sold=True, sold_to_id=2)
        rating = self._rating(listing_id=10)

        self.listing_db.update.return_value = listing
        self.rating_db.get_by_listing_id.return_value = rating

        out = self.mgr.update_listing(listing)

        self.assertIs(out, listing)
        self.assertIs(out.rating, rating)
        self.listing_db.update.assert_called_once_with(listing)
        self.rating_db.get_by_listing_id.assert_called_once_with(10)

    # -----------------------------
    # _populate_rating_if_available
    # exercised through public methods
    # -----------------------------
    def test_get_listing_by_id_returns_none_without_rating_lookup_when_listing_missing(self) -> None:
        self.listing_db.get_by_id.return_value = None

        out = self.mgr.get_listing_by_id(999)

        self.assertIsNone(out)
        self.rating_db.get_by_listing_id.assert_not_called()

    def test_create_listing_does_not_lookup_rating_when_created_listing_id_none(self) -> None:
        listing = self._listing(listing_id=None, is_sold=False)
        self.listing_db.add.return_value = listing

        out = self.mgr.create_listing(listing)

        self.assertIs(out, listing)
        self.rating_db.get_by_listing_id.assert_not_called()

    # -----------------------------
    # _populate_ratings_if_available
    # exercised through list methods
    # -----------------------------
    def test_list_listings_populates_ratings_for_each_listing_when_rating_db_available(self) -> None:
        l1 = self._listing(listing_id=1, is_sold=True, sold_to_id=2)
        l2 = self._listing(listing_id=2, is_sold=True, sold_to_id=3)
        r1 = self._rating(listing_id=1)
        r2 = self._rating(listing_id=2)

        self.listing_db.get_all.return_value = [l1, l2]
        self.rating_db.get_by_listing_id.side_effect = [r1, r2]

        out = self.mgr.list_listings()

        self.assertEqual(out, [l1, l2])
        self.assertIs(out[0].rating, r1)
        self.assertIs(out[1].rating, r2)
        self.assertEqual(self.rating_db.get_by_listing_id.call_count, 2)
        self.rating_db.get_by_listing_id.assert_any_call(1)
        self.rating_db.get_by_listing_id.assert_any_call(2)

    def test_list_listings_returns_same_list_without_rating_db(self) -> None:
        mgr = ListingManager(self.listing_db, self.comment_db, None)
        l1 = self._listing(listing_id=1, is_sold=False)
        l2 = self._listing(listing_id=2, is_sold=False)
        self.listing_db.get_all.return_value = [l1, l2]

        out = mgr.list_listings()

        self.assertEqual(out, [l1, l2])

    def test_list_recent_unsold_populates_ratings_when_rating_db_available(self) -> None:
        l1 = self._listing(listing_id=1, is_sold=True, sold_to_id=2)
        self.listing_db.get_recent_unsold.return_value = [l1]
        self.rating_db.get_by_listing_id.return_value = self._rating(listing_id=1)

        out = self.mgr.list_recent_unsold(limit=5, offset=0)

        self.assertEqual(out, [l1])
        self.assertIsNotNone(out[0].rating)
        self.rating_db.get_by_listing_id.assert_called_once_with(1)