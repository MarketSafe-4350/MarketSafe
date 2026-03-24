from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from src.business_logic.managers.rating import IRatingManager
from src.db.rating import RatingDB
from src.domain_models import Rating


class _RatingManagerCoverageShim(IRatingManager):
    # -----------------------------
    # CREATE
    # -----------------------------
    def create_rating(self, rating: Rating) -> Rating:
        return IRatingManager.create_rating(self, rating)

    # -----------------------------
    # READ (simple)
    # -----------------------------
    def get_rating_by_id(self, rating_id: int):
        return IRatingManager.get_rating_by_id(self, rating_id)

    def get_rating_by_listing_id(self, listing_id: int):
        return IRatingManager.get_rating_by_listing_id(self, listing_id)

    def list_ratings_by_rater(self, rater_id: int):
        return IRatingManager.list_ratings_by_rater(self, rater_id)

    def list_ratings(self):
        return IRatingManager.list_ratings(self)

    def list_recent_ratings(self, limit: int = 50, offset: int = 0):
        return IRatingManager.list_recent_ratings(self, limit, offset)

    def list_ratings_by_score(self, transaction_rating: int):
        return IRatingManager.list_ratings_by_score(self, transaction_rating)

    # -----------------------------
    # READ (aggregate)
    # -----------------------------
    def get_average_rating_by_account_id(self, account_id: int):
        return IRatingManager.get_average_rating_by_account_id(self, account_id)

    def get_sum_of_ratings_given_by_account_id(self, account_id: int):
        return IRatingManager.get_sum_of_ratings_given_by_account_id(self, account_id)

    def get_sum_of_ratings_received_by_account_id(self, account_id: int):
        return IRatingManager.get_sum_of_ratings_received_by_account_id(self, account_id)

    def count_ratings_received_by_account_id(self, account_id: int):
        return IRatingManager.count_ratings_received_by_account_id(self, account_id)

    def get_average_for_rater(self, rater_id: int):
        return IRatingManager.get_average_for_rater(self, rater_id)

    def count_by_rater(self, rater_id: int):
        return IRatingManager.count_by_rater(self, rater_id)

    # -----------------------------
    # UPDATE
    # -----------------------------
    def update_rating(self, rating: Rating) -> Rating:
        return IRatingManager.update_rating(self, rating)

    def update_rating_score(self, rating_id: int, transaction_rating: int):
        return IRatingManager.update_rating_score(self, rating_id, transaction_rating)

    # -----------------------------
    # DELETE
    # -----------------------------
    def delete_rating(self, rating_id: int):
        return IRatingManager.delete_rating(self, rating_id)

    def delete_rating_by_listing_id(self, listing_id: int):
        return IRatingManager.delete_rating_by_listing_id(self, listing_id)


class TestRatingManagerABC(unittest.TestCase):

    def setUp(self) -> None:
        self.rating_db = MagicMock(spec=RatingDB)
        self.sut = _RatingManagerCoverageShim(self.rating_db)

        self.sample_rating = Rating(
            listing_id=1,
            rater_id=2,
            transaction_rating=5,
            rating_id=None,
            created_at=None,
        )

    # -----------------------------
    # constructor
    # -----------------------------
    def test_init_stores_rating_db(self):
        self.assertIs(self.sut._rating_db, self.rating_db)

    # -----------------------------
    # CREATE
    # -----------------------------
    def test_create_rating_raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.sut.create_rating(self.sample_rating)

    # -----------------------------
    # READ
    # -----------------------------
    def test_get_rating_by_id_raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.sut.get_rating_by_id(1)

    def test_get_rating_by_listing_id_raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.sut.get_rating_by_listing_id(1)

    def test_list_ratings_by_rater_raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.sut.list_ratings_by_rater(2)

    def test_list_ratings_raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.sut.list_ratings()

    def test_list_recent_ratings_raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.sut.list_recent_ratings()

    def test_list_recent_ratings_with_args_raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.sut.list_recent_ratings(limit=10, offset=5)

    def test_list_ratings_by_score_raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.sut.list_ratings_by_score(5)

    # -----------------------------
    # aggregates
    # -----------------------------
    def test_get_average_rating_by_account_id_raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.sut.get_average_rating_by_account_id(1)

    def test_get_sum_of_ratings_given_by_account_id_raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.sut.get_sum_of_ratings_given_by_account_id(1)

    def test_get_sum_of_ratings_received_by_account_id_raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.sut.get_sum_of_ratings_received_by_account_id(1)

    def test_count_ratings_received_by_account_id_raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.sut.count_ratings_received_by_account_id(1)

    def test_get_average_for_rater_raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.sut.get_average_for_rater(1)

    def test_count_by_rater_raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.sut.count_by_rater(1)

    # -----------------------------
    # update
    # -----------------------------
    def test_update_rating_raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.sut.update_rating(self.sample_rating)

    def test_update_rating_score_raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.sut.update_rating_score(1, 4)

    # -----------------------------
    # delete
    # -----------------------------
    def test_delete_rating_raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.sut.delete_rating(1)

    def test_delete_rating_by_listing_id_raises_not_implemented_error(self):
        with self.assertRaises(NotImplementedError):
            self.sut.delete_rating_by_listing_id(1)