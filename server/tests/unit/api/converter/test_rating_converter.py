from __future__ import annotations

import unittest

from pydantic import ValidationError as PydanticValidationError

from src.api.converter.rating_converter import RatingCreate, RatingResponse
from src.domain_models.rating import Rating


class TestRatingConverter(unittest.TestCase):
    # -----------------------------
    # RatingCreate (pydantic validation)
    # -----------------------------
    def test_rating_create_valid_min_score(self) -> None:
        dto = RatingCreate(transaction_rating=1)
        self.assertEqual(dto.transaction_rating, 1)

    def test_rating_create_valid_max_score(self) -> None:
        dto = RatingCreate(transaction_rating=5)
        self.assertEqual(dto.transaction_rating, 5)

    def test_rating_create_valid_mid_score(self) -> None:
        dto = RatingCreate(transaction_rating=3)
        self.assertEqual(dto.transaction_rating, 3)

    def test_rating_create_rejects_score_below_minimum(self) -> None:
        with self.assertRaises(PydanticValidationError):
            RatingCreate(transaction_rating=0)

    def test_rating_create_rejects_score_above_maximum(self) -> None:
        with self.assertRaises(PydanticValidationError):
            RatingCreate(transaction_rating=6)

    def test_rating_create_rejects_negative_score(self) -> None:
        with self.assertRaises(PydanticValidationError):
            RatingCreate(transaction_rating=-1)

    # -----------------------------
    # RatingResponse.from_domain
    # -----------------------------
    def test_rating_response_from_domain_maps_all_fields(self) -> None:
        rating = Rating(
            listing_id=10,
            rater_id=2,
            transaction_rating=4,
            rating_id=99,
        )

        out = RatingResponse.from_domain(rating)

        self.assertIsInstance(out, RatingResponse)
        self.assertEqual(out.id, 99)
        self.assertEqual(out.listing_id, 10)
        self.assertEqual(out.rater_id, 2)
        self.assertEqual(out.transaction_rating, 4)

    def test_rating_response_from_domain_id_is_none_before_persistence(self) -> None:
        rating = Rating(
            listing_id=1,
            rater_id=3,
            transaction_rating=5,
            rating_id=None,
        )

        out = RatingResponse.from_domain(rating)

        self.assertIsNone(out.id)
        self.assertEqual(out.listing_id, 1)
        self.assertEqual(out.rater_id, 3)
        self.assertEqual(out.transaction_rating, 5)

    def test_rating_response_from_domain_maps_min_transaction_rating(self) -> None:
        rating = Rating(
            listing_id=5,
            rater_id=1,
            transaction_rating=1,
            rating_id=7,
        )

        out = RatingResponse.from_domain(rating)

        self.assertEqual(out.transaction_rating, 1)

    def test_rating_response_from_domain_maps_max_transaction_rating(self) -> None:
        rating = Rating(
            listing_id=5,
            rater_id=1,
            transaction_rating=5,
            rating_id=7,
        )

        out = RatingResponse.from_domain(rating)

        self.assertEqual(out.transaction_rating, 5)
