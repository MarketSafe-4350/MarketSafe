from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from src.business_logic.managers.rating import RatingManager
from src.domain_models import Rating
from src.utils import ValidationError


class TestRatingManagerUnit(unittest.TestCase):
    def setUp(self) -> None:
        self.rating_db = MagicMock()
        self.manager = RatingManager(self.rating_db)

    # -----------------------------
    # CREATE
    # -----------------------------
    def test_create_rating_returns_created_rating(self) -> None:
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=5)
        created = Rating(listing_id=1, rater_id=2, transaction_rating=5, rating_id=10)
        self.rating_db.add.return_value = created

        out = self.manager.create_rating(rating)

        self.assertIs(created, out)
        self.rating_db.add.assert_called_once_with(rating)

    def test_create_rating_raises_validation_error_when_rating_is_none(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.create_rating(None)  # type: ignore[arg-type]

    # -----------------------------
    # READ (simple)
    # -----------------------------
    def test_get_rating_by_id_returns_rating(self) -> None:
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=5, rating_id=10)
        self.rating_db.get_by_id.return_value = rating

        out = self.manager.get_rating_by_id(10)

        self.assertIs(rating, out)
        self.rating_db.get_by_id.assert_called_once_with(10)

    def test_get_rating_by_id_raises_validation_error_when_rating_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get_rating_by_id(None)  # type: ignore[arg-type]

    def test_get_rating_by_listing_id_returns_rating(self) -> None:
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=5, rating_id=10)
        self.rating_db.get_by_listing_id.return_value = rating

        out = self.manager.get_rating_by_listing_id(1)

        self.assertIs(rating, out)
        self.rating_db.get_by_listing_id.assert_called_once_with(1)

    def test_get_rating_by_listing_id_raises_validation_error_when_listing_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get_rating_by_listing_id(None)  # type: ignore[arg-type]

    def test_list_ratings_by_rater_returns_ratings(self) -> None:
        ratings = [
            Rating(listing_id=1, rater_id=2, transaction_rating=5, rating_id=10),
            Rating(listing_id=2, rater_id=2, transaction_rating=4, rating_id=11),
        ]
        self.rating_db.get_by_rater_id.return_value = ratings

        out = self.manager.list_ratings_by_rater(2)

        self.assertEqual(ratings, out)
        self.rating_db.get_by_rater_id.assert_called_once_with(2)

    def test_list_ratings_by_rater_raises_validation_error_when_rater_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.list_ratings_by_rater(None)  # type: ignore[arg-type]

    def test_list_ratings_returns_all_ratings(self) -> None:
        ratings = [
            Rating(listing_id=1, rater_id=2, transaction_rating=5, rating_id=10),
            Rating(listing_id=2, rater_id=3, transaction_rating=4, rating_id=11),
        ]
        self.rating_db.get_all.return_value = ratings

        out = self.manager.list_ratings()

        self.assertEqual(ratings, out)
        self.rating_db.get_all.assert_called_once_with()

    def test_list_recent_ratings_returns_recent_ratings(self) -> None:
        ratings = [
            Rating(listing_id=1, rater_id=2, transaction_rating=5, rating_id=10),
        ]
        self.rating_db.get_recent.return_value = ratings

        out = self.manager.list_recent_ratings(limit=5, offset=2)

        self.assertEqual(ratings, out)
        self.rating_db.get_recent.assert_called_once_with(limit=5, offset=2)

    def test_list_recent_ratings_raises_validation_error_when_limit_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.list_recent_ratings(limit=None, offset=0)  # type: ignore[arg-type]

    def test_list_recent_ratings_raises_validation_error_when_offset_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.list_recent_ratings(limit=10, offset=None)  # type: ignore[arg-type]

    def test_list_ratings_by_score_returns_ratings(self) -> None:
        ratings = [
            Rating(listing_id=1, rater_id=2, transaction_rating=5, rating_id=10),
        ]
        self.rating_db.get_by_score.return_value = ratings

        out = self.manager.list_ratings_by_score(5)

        self.assertEqual(ratings, out)
        self.rating_db.get_by_score.assert_called_once_with(5)

    def test_list_ratings_by_score_raises_validation_error_when_score_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.list_ratings_by_score(None)  # type: ignore[arg-type]

    # -----------------------------
    # READ (aggregate / statistics)
    # -----------------------------
    def test_get_average_rating_by_account_id_returns_average(self) -> None:
        self.rating_db.get_average_rating_by_account_id.return_value = 4.25

        out = self.manager.get_average_rating_by_account_id(1)

        self.assertEqual(4.25, out)
        self.rating_db.get_average_rating_by_account_id.assert_called_once_with(1)

    def test_get_average_rating_by_account_id_raises_validation_error_when_account_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get_average_rating_by_account_id(None)  # type: ignore[arg-type]

    def test_get_sum_of_ratings_given_by_account_id_returns_sum(self) -> None:
        self.rating_db.get_sum_of_ratings_given_by_account_id.return_value = 15

        out = self.manager.get_sum_of_ratings_given_by_account_id(1)

        self.assertEqual(15, out)
        self.rating_db.get_sum_of_ratings_given_by_account_id.assert_called_once_with(1)

    def test_get_sum_of_ratings_given_by_account_id_raises_validation_error_when_account_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get_sum_of_ratings_given_by_account_id(None)  # type: ignore[arg-type]

    def test_get_sum_of_ratings_received_by_account_id_returns_sum(self) -> None:
        self.rating_db.get_sum_of_ratings_received_by_account_id.return_value = 22

        out = self.manager.get_sum_of_ratings_received_by_account_id(1)

        self.assertEqual(22, out)
        self.rating_db.get_sum_of_ratings_received_by_account_id.assert_called_once_with(1)

    def test_get_sum_of_ratings_received_by_account_id_raises_validation_error_when_account_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get_sum_of_ratings_received_by_account_id(None)  # type: ignore[arg-type]

    def test_count_ratings_received_by_account_id_returns_count(self) -> None:
        self.rating_db.count_ratings_received_by_account_id.return_value = 3

        out = self.manager.count_ratings_received_by_account_id(1)

        self.assertEqual(3, out)
        self.rating_db.count_ratings_received_by_account_id.assert_called_once_with(1)

    def test_count_ratings_received_by_account_id_raises_validation_error_when_account_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.count_ratings_received_by_account_id(None)  # type: ignore[arg-type]

    def test_get_average_for_rater_returns_average(self) -> None:
        self.rating_db.get_average_for_rater.return_value = 3.5

        out = self.manager.get_average_for_rater(2)

        self.assertEqual(3.5, out)
        self.rating_db.get_average_for_rater.assert_called_once_with(2)

    def test_get_average_for_rater_raises_validation_error_when_rater_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get_average_for_rater(None)  # type: ignore[arg-type]

    def test_count_by_rater_returns_count(self) -> None:
        self.rating_db.count_by_rater.return_value = 7

        out = self.manager.count_by_rater(2)

        self.assertEqual(7, out)
        self.rating_db.count_by_rater.assert_called_once_with(2)

    def test_count_by_rater_raises_validation_error_when_rater_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.count_by_rater(None)  # type: ignore[arg-type]

    # -----------------------------
    # UPDATE
    # -----------------------------
    def test_update_rating_returns_updated_rating(self) -> None:
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=5, rating_id=10)
        updated = Rating(listing_id=1, rater_id=2, transaction_rating=4, rating_id=10)
        self.rating_db.update.return_value = updated

        out = self.manager.update_rating(rating)

        self.assertIs(updated, out)
        self.rating_db.update.assert_called_once_with(rating)

    def test_update_rating_raises_validation_error_when_rating_is_none(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.update_rating(None)  # type: ignore[arg-type]

    def test_update_rating_raises_validation_error_when_rating_id_is_none(self) -> None:
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=5)

        with self.assertRaises(ValidationError):
            self.manager.update_rating(rating)

    def test_update_rating_score_delegates_to_db(self) -> None:
        out = self.manager.update_rating_score(10, 4)

        self.assertIsNone(out)
        self.rating_db.set_score.assert_called_once_with(10, 4)

    def test_update_rating_score_raises_validation_error_when_rating_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.update_rating_score(None, 4)  # type: ignore[arg-type]

    def test_update_rating_score_raises_validation_error_when_transaction_rating_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.update_rating_score(10, None)  # type: ignore[arg-type]

    # -----------------------------
    # DELETE
    # -----------------------------
    def test_delete_rating_returns_true(self) -> None:
        self.rating_db.remove.return_value = True

        out = self.manager.delete_rating(10)

        self.assertTrue(out)
        self.rating_db.remove.assert_called_once_with(10)

    def test_delete_rating_raises_validation_error_when_rating_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.delete_rating(None)  # type: ignore[arg-type]

    def test_delete_rating_by_listing_id_returns_true(self) -> None:
        self.rating_db.remove_by_listing_id.return_value = True

        out = self.manager.delete_rating_by_listing_id(1)

        self.assertTrue(out)
        self.rating_db.remove_by_listing_id.assert_called_once_with(1)

    def test_delete_rating_by_listing_id_raises_validation_error_when_listing_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.delete_rating_by_listing_id(None)  # type: ignore[arg-type]