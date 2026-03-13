from __future__ import annotations

import unittest
from datetime import datetime

from src.db.utils.rating_mapper import RatingMapper
from src.domain_models import Rating


class TestRatingMapper(unittest.TestCase):

    def test_from_mapping_creates_rating_object(self) -> None:
        created_at = datetime.now()

        mapping = {
            "id": 10,
            "listing_id": 20,
            "rater_id": 30,
            "transaction_rating": 5,
            "created_at": created_at,
        }

        rating = RatingMapper.from_mapping(mapping)

        self.assertIsInstance(rating, Rating)
        self.assertEqual(10, rating.id)
        self.assertEqual(20, rating.listing_id)
        self.assertEqual(30, rating.rater_id)
        self.assertEqual(5, rating.transaction_rating)
        self.assertEqual(created_at, rating.created_at)