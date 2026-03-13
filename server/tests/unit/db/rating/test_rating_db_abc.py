from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from src.db import DBUtility
from src.db.rating import RatingDB
from src.domain_models import Rating


class _RatingDBCoverageShim(RatingDB):
    # -----------------------------
    # inherited abstract methods from BaseRatingDB
    # -----------------------------
    def get_average_rating_by_account_id(self, account_id: int) -> float | None:
        return RatingDB.get_average_rating_by_account_id(self, account_id)

    def get_sum_of_ratings_given_by_account_id(self, account_id: int) -> int:
        return RatingDB.get_sum_of_ratings_given_by_account_id(self, account_id)

    def get_sum_of_ratings_received_by_account_id(self, account_id: int) -> int:
        return RatingDB.get_sum_of_ratings_received_by_account_id(self, account_id)

    def get_by_listing_id(self, listing_id: int) -> Rating | None:
        return RatingDB.get_by_listing_id(self, listing_id)

    def get_by_rater_id(self, rater_id: int):
        return RatingDB.get_by_rater_id(self, rater_id)

    # -----------------------------
    # RatingDB abstract methods
    # -----------------------------
    def add(self, rating: Rating) -> Rating:
        return RatingDB.add(self, rating)

    def get_by_id(self, rating_id: int) -> Rating | None:
        return RatingDB.get_by_id(self, rating_id)

    def get_all(self):
        return RatingDB.get_all(self)

    def get_recent(self, limit: int = 50, offset: int = 0):
        return RatingDB.get_recent(self, limit, offset)

    def get_by_score(self, transaction_rating: int):
        return RatingDB.get_by_score(self, transaction_rating)

    def get_average_for_rater(self, rater_id: int) -> float | None:
        return RatingDB.get_average_for_rater(self, rater_id)

    def count_by_rater(self, rater_id: int) -> int:
        return RatingDB.count_by_rater(self, rater_id)

    def update(self, rating: Rating) -> Rating:
        return RatingDB.update(self, rating)

    def set_score(self, rating_id: int, transaction_rating: int) -> None:
        return RatingDB.set_score(self, rating_id, transaction_rating)

    def remove(self, rating_id: int) -> bool:
        return RatingDB.remove(self, rating_id)

    def remove_by_listing_id(self, listing_id: int) -> bool:
        return RatingDB.remove_by_listing_id(self, listing_id)


class TestRatingDBABC(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock(spec=DBUtility)
        self.sut = _RatingDBCoverageShim(self.db)

        self.sample_rating = Rating(
            listing_id=1,
            rater_id=2,
            transaction_rating=5,
            rating_id=None,
            created_at=None,
        )

    # -----------------------------
    # __init__
    # -----------------------------
    def test_init_stores_db(self) -> None:
        self.assertIs(self.sut._db, self.db)

    # -----------------------------
    # inherited BaseRatingDB methods
    # -----------------------------
    def test_get_average_rating_by_account_id_raises_not_implemented_error(
        self,
    ) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_average_rating_by_account_id(1)

    def test_get_sum_of_ratings_given_by_account_id_raises_not_implemented_error(
        self,
    ) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_sum_of_ratings_given_by_account_id(1)

    def test_get_sum_of_ratings_received_by_account_id_raises_not_implemented_error(
        self,
    ) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_sum_of_ratings_received_by_account_id(1)

    def test_get_by_listing_id_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_by_listing_id(1)

    def test_get_by_rater_id_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_by_rater_id(2)

    # -----------------------------
    # RatingDB methods
    # -----------------------------
    def test_add_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.add(self.sample_rating)

    def test_get_by_id_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_by_id(1)

    def test_get_all_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_all()

    def test_get_recent_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_recent()

    def test_get_recent_with_args_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_recent(limit=10, offset=5)

    def test_get_by_score_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_by_score(5)

    def test_get_average_for_rater_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_average_for_rater(2)

    def test_count_by_rater_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.count_by_rater(2)

    def test_update_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.update(self.sample_rating)

    def test_set_score_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.set_score(1, 4)

    def test_remove_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.remove(1)

    def test_remove_by_listing_id_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.remove_by_listing_id(1)