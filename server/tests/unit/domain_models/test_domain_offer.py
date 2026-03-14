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

from src.domain_models.offer import Offer
from src.utils import ValidationError, UnapprovedBehaviorError


class TestOffer(unittest.TestCase):

    # ==============================
    # __init__
    # ==============================

    def test_minimal_required_fields(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=50.0)

        self.assertIsNone(offer.id)
        self.assertEqual(offer.listing_id, 1)
        self.assertEqual(offer.sender_id, 2)
        self.assertEqual(offer.offered_price, 50.0)
        self.assertIsNone(offer.location_offered)
        self.assertIsNone(offer.created_date)
        self.assertFalse(offer.seen)
        self.assertIsNone(offer.accepted)
        self.assertTrue(offer.is_pending)

    def test_all_optional_fields(self):
        offer = Offer(
            listing_id=5,
            sender_id=10,
            offered_price=99.99,
            offer_id=7,
            location_offered="123 Main St",
            created_date="2026-01-01",
            seen=True,
            accepted=True,
        )

        self.assertEqual(offer.id, 7)
        self.assertEqual(offer.location_offered, "123 Main St")
        self.assertEqual(offer.created_date, "2026-01-01")
        self.assertTrue(offer.seen)
        self.assertTrue(offer.accepted)
        self.assertFalse(offer.is_pending)

    def test_accepted_false_at_init(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0, accepted=False)
        self.assertFalse(offer.accepted)
        self.assertFalse(offer.is_pending)

    def test_init_raises_when_listing_id_not_int(self):
        with self.assertRaises(ValidationError):
            Offer(listing_id="bad", sender_id=2, offered_price=10.0)

    def test_init_raises_when_sender_id_not_int(self):
        with self.assertRaises(ValidationError):
            Offer(listing_id=1, sender_id="bad", offered_price=10.0)

    def test_init_raises_when_offered_price_zero(self):
        with self.assertRaises(ValidationError):
            Offer(listing_id=1, sender_id=2, offered_price=0)

    def test_init_raises_when_offered_price_negative(self):
        with self.assertRaises(ValidationError):
            Offer(listing_id=1, sender_id=2, offered_price=-5.0)

    def test_init_raises_when_accepted_is_string(self):
        with self.assertRaises(ValidationError):
            Offer(listing_id=1, sender_id=2, offered_price=10.0, accepted="yes")

    def test_init_raises_when_accepted_is_int(self):
        with self.assertRaises(ValidationError):
            Offer(listing_id=1, sender_id=2, offered_price=10.0, accepted=1)

    def test_init_raises_when_seen_not_bool(self):
        with self.assertRaises(ValidationError):
            Offer(listing_id=1, sender_id=2, offered_price=10.0, seen="yes")

    # ==============================
    # mark_persisted
    # ==============================

    def test_mark_persisted_assigns_id(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        offer.mark_persisted(42)
        self.assertEqual(offer.id, 42)

    def test_mark_persisted_raises_when_none(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        with self.assertRaises(ValidationError):
            offer.mark_persisted(None)

    def test_mark_persisted_raises_when_already_assigned(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0, offer_id=5)
        with self.assertRaises(UnapprovedBehaviorError):
            offer.mark_persisted(10)

    # ==============================
    # listing_id setter
    # ==============================

    def test_listing_id_setter_updates_value(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        offer.listing_id = 99
        self.assertEqual(offer.listing_id, 99)

    def test_listing_id_setter_raises_when_not_int(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        with self.assertRaises(ValidationError):
            offer.listing_id = "bad"

    # ==============================
    # sender_id setter
    # ==============================

    def test_sender_id_setter_updates_value(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        offer.sender_id = 77
        self.assertEqual(offer.sender_id, 77)

    def test_sender_id_setter_raises_when_not_int(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        with self.assertRaises(ValidationError):
            offer.sender_id = 3.5

    # ==============================
    # offered_price setter
    # ==============================

    def test_offered_price_setter_updates_value(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        offer.offered_price = 200.0
        self.assertEqual(offer.offered_price, 200.0)

    def test_offered_price_setter_raises_when_zero(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        with self.assertRaises(ValidationError):
            offer.offered_price = 0

    def test_offered_price_setter_raises_when_negative(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        with self.assertRaises(ValidationError):
            offer.offered_price = -1.0

    # ==============================
    # location_offered setter
    # ==============================

    def test_location_offered_setter_updates_to_string(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        offer.location_offered = "456 Oak Ave"
        self.assertEqual(offer.location_offered, "456 Oak Ave")

    def test_location_offered_setter_accepts_none(self):
        offer = Offer(
            listing_id=1, sender_id=2, offered_price=10.0, location_offered="somewhere"
        )
        offer.location_offered = None
        self.assertIsNone(offer.location_offered)

    def test_location_offered_setter_raises_when_not_str(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        with self.assertRaises(ValidationError):
            offer.location_offered = 123

    # ==============================
    # created_date
    # ==============================

    def test_created_date_returns_value(self):
        offer = Offer(
            listing_id=1, sender_id=2, offered_price=10.0, created_date="2026-03-01"
        )
        self.assertEqual(offer.created_date, "2026-03-01")

    def test_created_date_defaults_to_none(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        self.assertIsNone(offer.created_date)

    # ==============================
    # seen / mark_seen
    # ==============================

    def test_seen_defaults_false(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        self.assertFalse(offer.seen)

    def test_mark_seen_sets_true(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        offer.mark_seen()
        self.assertTrue(offer.seen)

    def test_mark_seen_is_idempotent(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        offer.mark_seen()
        offer.mark_seen()
        self.assertTrue(offer.seen)

    # ==============================
    # accept / reject
    # ==============================

    def test_accept_sets_accepted_true(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        offer.accept()
        self.assertTrue(offer.accepted)
        self.assertFalse(offer.is_pending)

    def test_reject_sets_accepted_false(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        offer.reject()
        self.assertFalse(offer.accepted)
        self.assertFalse(offer.is_pending)

    def test_accept_raises_when_already_accepted(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        offer.accept()
        with self.assertRaises(UnapprovedBehaviorError):
            offer.accept()

    def test_accept_raises_when_already_rejected(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        offer.reject()
        with self.assertRaises(UnapprovedBehaviorError):
            offer.accept()

    def test_reject_raises_when_already_rejected(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        offer.reject()
        with self.assertRaises(UnapprovedBehaviorError):
            offer.reject()

    def test_reject_raises_when_already_accepted(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        offer.accept()
        with self.assertRaises(UnapprovedBehaviorError):
            offer.reject()

    def test_is_pending_true_when_accepted_is_none(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        self.assertTrue(offer.is_pending)

    # ==============================
    # __repr__
    # ==============================

    def test_repr_contains_all_fields(self):
        offer = Offer(
            listing_id=3,
            sender_id=7,
            offered_price=150.0,
            offer_id=11,
            location_offered="campus",
            created_date="2026-02-01",
            seen=True,
            accepted=False,
        )
        out = repr(offer)

        self.assertIn("Offer(id=11", out)
        self.assertIn("listing_id=3", out)
        self.assertIn("sender_id=7", out)
        self.assertIn("offered_price=150.0", out)
        self.assertIn("location_offered='campus'", out)
        self.assertIn("seen=True", out)
        self.assertIn("accepted=False", out)
        self.assertIn("created_date='2026-02-01'", out)

    def test_repr_with_none_fields(self):
        offer = Offer(listing_id=1, sender_id=2, offered_price=10.0)
        out = repr(offer)
        self.assertIn("Offer(id=None", out)
        self.assertIn("location_offered=None", out)
        self.assertIn("accepted=None", out)
