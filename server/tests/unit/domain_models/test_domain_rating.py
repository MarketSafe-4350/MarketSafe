import os
from pathlib import Path
import sys
import types
import unittest

sys.modules.setdefault(
    "dotenv", types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None)
)
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from src.domain_models import Rating
from src.utils import ValidationError, UnapprovedBehaviorError


class TestRating(unittest.TestCase):

    # ==============================
    # __init__
    # ==============================

    def test_init_sets_all_fields(self):
        rating = Rating(
            listing_id=10,
            rater_id=20,
            transaction_rating=5,
            rating_id=1,
            created_at="2026-03-12",
        )

        self.assertEqual(rating.id, 1)
        self.assertEqual(rating.listing_id, 10)
        self.assertEqual(rating.rater_id, 20)
        self.assertEqual(rating.transaction_rating, 5)
        self.assertEqual(rating.created_at, "2026-03-12")

    def test_init_raises_when_transaction_rating_out_of_range(self):
        with self.assertRaises(ValidationError):
            Rating(listing_id=1, rater_id=2, transaction_rating=7)

    # ==============================
    # mark_persisted
    # ==============================

    def test_mark_persisted_sets_id(self):
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=3)
        rating.mark_persisted(99)
        self.assertEqual(rating.id, 99)

    def test_mark_persisted_raises_when_none(self):
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=3)
        with self.assertRaises(ValidationError):
            rating.mark_persisted(None)

    def test_mark_persisted_raises_when_already_assigned(self):
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=3, rating_id=10)
        with self.assertRaises(UnapprovedBehaviorError):
            rating.mark_persisted(20)

    # ==============================
    # listing_id setter
    # ==============================

    def test_listing_id_setter_updates_value(self):
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=3)
        rating.listing_id = 50
        self.assertEqual(rating.listing_id, 50)

    def test_listing_id_setter_raises_when_not_int(self):
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=3)
        with self.assertRaises(ValidationError):
            rating.listing_id = "50"

    # ==============================
    # rater_id setter
    # ==============================

    def test_rater_id_setter_updates_value(self):
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=3)
        rating.rater_id = 70
        self.assertEqual(rating.rater_id, 70)

    def test_rater_id_setter_raises_when_not_int(self):
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=3)
        with self.assertRaises(ValidationError):
            rating.rater_id = "70"

    # ==============================
    # transaction_rating setter
    # ==============================

    def test_transaction_rating_setter_updates_value(self):
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=3)
        rating.transaction_rating = 5
        self.assertEqual(rating.transaction_rating, 5)

    def test_transaction_rating_setter_raises_when_below_range(self):
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=3)
        with self.assertRaises(ValidationError):
            rating.transaction_rating = 0

    def test_transaction_rating_setter_raises_when_above_range(self):
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=3)
        with self.assertRaises(ValidationError):
            rating.transaction_rating = 6

    def test_transaction_rating_setter_raises_when_not_int(self):
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=3)
        with self.assertRaises(ValidationError):
            rating.transaction_rating = "5"

    # ==============================
    # created_at
    # ==============================

    def test_created_at_returns_value(self):
        rating = Rating(
            listing_id=1,
            rater_id=2,
            transaction_rating=4,
            created_at="2026-03-12 10:00:00",
        )
        self.assertEqual(rating.created_at, "2026-03-12 10:00:00")

    # ==============================
    # __repr__
    # ==============================

    def test_repr_contains_all_fields(self):
        rating = Rating(
            listing_id=11,
            rater_id=22,
            transaction_rating=4,
            rating_id=33,
            created_at="2026-03-12",
        )
        out = repr(rating)

        self.assertIn("Rating(", out)
        self.assertIn("id=33", out)
        self.assertIn("listing_id=11", out)
        self.assertIn("rater_id=22", out)
        self.assertIn("transaction_rating=4", out)
        self.assertIn("created_at='2026-03-12'", out)
