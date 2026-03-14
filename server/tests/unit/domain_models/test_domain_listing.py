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

from src.domain_models import Listing, Comment, Rating, Offer
from src.utils import ValidationError, UnapprovedBehaviorError


class TestListing(unittest.TestCase):

    # ==============================
    # properties, mutators, repr
    # ==============================

    def test_properties_mutators_mark_persisted_and_repr(self):
        listing = Listing(
            seller_id=1,
            title=" title ",
            description=" desc ",
            price=10,
            listing_id=None,
            image_url=" image.jpg ",
            location=" Winnipeg ",
            created_at="2026-01-01",
            comments=[],
        )

        self.assertIsNone(listing.id)
        self.assertEqual(listing.seller_id, 1)
        self.assertEqual(listing.title, "title")
        self.assertEqual(listing.description, "desc")
        self.assertEqual(listing.price, 10.0)
        self.assertEqual(listing.image_url, "image.jpg")
        self.assertEqual(listing.location, "Winnipeg")
        self.assertEqual(listing.created_at, "2026-01-01")
        self.assertFalse(listing.is_sold)
        self.assertIsNone(listing.sold_to_id)
        self.assertEqual(listing.comments, [])

        listing.mark_persisted(100)
        self.assertEqual(listing.id, 100)

        listing.seller_id = 2
        listing.title = " New Title "
        listing.description = " New Desc "
        listing.image_url = None
        listing.image_url = " img2.png "
        listing.price = 25
        listing.location = None
        listing.location = " Campus "

        self.assertEqual(listing.seller_id, 2)
        self.assertEqual(listing.title, "New Title")
        self.assertEqual(listing.description, "New Desc")
        self.assertEqual(listing.image_url, "img2.png")
        self.assertEqual(listing.price, 25.0)
        self.assertEqual(listing.location, "Campus")

        rep = repr(listing)
        self.assertIn("Listing(id=100", rep)

    # ==============================
    # mark_persisted
    # ==============================

    def test_mark_persisted_raises_when_none(self):
        listing = Listing(1, "t", "d", 1.0, comments=[])
        with self.assertRaises(ValidationError):
            listing.mark_persisted(None)

    def test_mark_persisted_raises_when_already_assigned(self):
        listing = Listing(1, "t", "d", 1.0, comments=[])
        listing.mark_persisted(1)
        with self.assertRaises(UnapprovedBehaviorError):
            listing.mark_persisted(2)

    # ==============================
    # sold state
    # ==============================

    def test_constructor_enforces_sold_invariants(self):
        with self.assertRaises(ValidationError):
            Listing(1, "t", "d", 2.0, is_sold=True, sold_to_id=None, comments=[])

        with self.assertRaises(ValidationError):
            Listing(1, "t", "d", 2.0, is_sold=False, sold_to_id=3, comments=[])

    def test_mark_sold_success(self):
        listing = Listing(1, "t", "d", 1.0, comments=[])
        listing.mark_sold(4)
        self.assertTrue(listing.is_sold)
        self.assertEqual(listing.sold_to_id, 4)

    def test_mark_sold_raises_when_already_sold(self):
        listing = Listing(1, "t", "d", 1.0, comments=[])
        listing.mark_sold(4)
        with self.assertRaises(UnapprovedBehaviorError):
            listing.mark_sold(5)

    # ==============================
    # comments
    # ==============================

    def test_comments_setter_accepts_none(self):
        listing = Listing(1, "t", "d", 1.0, comments=[])
        listing.comments = None
        self.assertEqual(listing.comments, [])

    def test_comments_setter_raises_when_not_list(self):
        listing = Listing(1, "t", "d", 1.0, comments=[])
        with self.assertRaises(ValidationError):
            listing.comments = "not-a-list"

    def test_comments_setter_raises_when_item_not_comment(self):
        listing = Listing(1, "t", "d", 1.0, comments=[])
        with self.assertRaises(ValidationError):
            listing.comments = ["bad-item"]

    def test_comments_setter_returns_defensive_copy(self):
        comment = Comment(1, 2, body="ok")
        original = [comment]
        listing = Listing(1, "t", "d", 1.0, comments=[])
        listing.comments = original
        original.clear()
        self.assertEqual(len(listing.comments), 1)

    def test_add_comment_success(self):
        listing = Listing(1, "t", "d", 1.0, listing_id=10, comments=[])
        c = Comment(10, 2, body="a")
        listing.add_comment(c)
        self.assertIs(listing.comments[-1], c)

    def test_add_comment_raises_when_none(self):
        listing = Listing(1, "t", "d", 1.0, listing_id=10, comments=[])
        with self.assertRaises(ValidationError):
            listing.add_comment(None)

    def test_add_comments_success(self):
        listing = Listing(1, "t", "d", 1.0, listing_id=10, comments=[])
        c = Comment(10, 3, body="b")
        listing.add_comments([c])
        self.assertIs(listing.comments[-1], c)

    def test_add_comments_raises_when_none(self):
        listing = Listing(1, "t", "d", 1.0, listing_id=10, comments=[])
        with self.assertRaises(ValidationError):
            listing.add_comments(None)

    def test_add_comments_raises_when_not_list(self):
        listing = Listing(1, "t", "d", 1.0, listing_id=10, comments=[])
        with self.assertRaises(ValidationError):
            listing.add_comments("nope")

    def test_add_comments_raises_when_item_not_comment(self):
        listing = Listing(1, "t", "d", 1.0, listing_id=10, comments=[])
        with self.assertRaises(ValidationError):
            listing.add_comments(["bad-item"])

    def test_add_comments_raises_when_listing_id_mismatch(self):
        listing = Listing(1, "t", "d", 1.0, listing_id=10, comments=[])
        with self.assertRaises(ValidationError):
            listing.add_comments([Comment(999, 2, body="wrong listing")])

    # ==============================
    # rating
    # ==============================

    def test_rating_property_returns_none_by_default(self):
        listing = Listing(1, "t", "d", 1.0, comments=[])
        self.assertIsNone(listing.rating)

    def test_rating_setter_accepts_none(self):
        listing = Listing(1, "t", "d", 1.0, comments=[])
        listing.rating = None
        self.assertIsNone(listing.rating)

    def test_rating_setter_raises_when_listing_not_sold(self):
        rating = Rating(listing_id=10, rater_id=2, transaction_rating=5)
        listing = Listing(1, "t", "d", 1.0, listing_id=10, comments=[])
        with self.assertRaises(ValidationError):
            listing.rating = rating

    def test_rating_setter_accepts_when_sold_and_matching_listing_id(self):
        rating = Rating(listing_id=10, rater_id=2, transaction_rating=5)
        listing = Listing(
            1, "t", "d", 1.0, listing_id=10, is_sold=True, sold_to_id=2, comments=[]
        )
        listing.rating = rating
        self.assertIs(listing.rating, rating)

    def test_rating_setter_raises_when_listing_id_mismatch(self):
        rating = Rating(listing_id=999, rater_id=2, transaction_rating=5)
        listing = Listing(
            1, "t", "d", 1.0, listing_id=10, is_sold=True, sold_to_id=2, comments=[]
        )
        with self.assertRaises(ValidationError):
            listing.rating = rating

    def test_add_rating_success(self):
        rating = Rating(listing_id=10, rater_id=2, transaction_rating=5)
        listing = Listing(
            1, "t", "d", 1.0, listing_id=10, is_sold=True, sold_to_id=2, comments=[]
        )
        listing.add_rating(rating)
        self.assertIs(listing.rating, rating)

    def test_add_rating_raises_when_none(self):
        listing = Listing(
            1, "t", "d", 1.0, listing_id=10, is_sold=True, sold_to_id=2, comments=[]
        )
        with self.assertRaises(ValidationError):
            listing.add_rating(None)

    def test_add_rating_raises_when_already_exists(self):
        rating1 = Rating(listing_id=10, rater_id=2, transaction_rating=5)
        rating2 = Rating(listing_id=10, rater_id=2, transaction_rating=4)
        listing = Listing(
            1, "t", "d", 1.0, listing_id=10, is_sold=True, sold_to_id=2, comments=[]
        )
        listing.add_rating(rating1)
        with self.assertRaises(UnapprovedBehaviorError):
            listing.add_rating(rating2)

    def test_remove_rating_clears_rating(self):
        rating = Rating(listing_id=10, rater_id=2, transaction_rating=5)
        listing = Listing(
            1, "t", "d", 1.0, listing_id=10, is_sold=True, sold_to_id=2, comments=[]
        )
        listing.add_rating(rating)
        listing.remove_rating()
        self.assertIsNone(listing.rating)

    def test_mark_persisted_rechecks_rating_invariants(self):
        rating = Rating(listing_id=999, rater_id=2, transaction_rating=5)
        listing = Listing(
            1, "t", "d", 1.0, is_sold=True, sold_to_id=2, rating=rating, comments=[]
        )
        with self.assertRaises(ValidationError):
            listing.mark_persisted(10)

    # ==============================
    # offers
    # ==============================

    def test_offers_empty_by_default(self):
        listing = Listing(1, "t", "d", 1.0)
        self.assertEqual(listing.offers, [])

    def test_init_with_offers(self):
        offer = Offer(listing_id=10, sender_id=3, offered_price=25.0)
        listing = Listing(1, "t", "d", 1.0, listing_id=10, offers=[offer])
        self.assertEqual(len(listing.offers), 1)
        self.assertIs(listing.offers[0], offer)

    def test_offers_returns_defensive_copy(self):
        offer = Offer(listing_id=10, sender_id=3, offered_price=25.0)
        listing = Listing(1, "t", "d", 1.0, listing_id=10, offers=[offer])
        copy = listing.offers
        copy.clear()
        self.assertEqual(len(listing.offers), 1)

    def test_offers_setter_accepts_list(self):
        listing = Listing(1, "t", "d", 1.0)
        offer = Offer(listing_id=10, sender_id=3, offered_price=25.0)
        listing.offers = [offer]
        self.assertEqual(len(listing.offers), 1)

    def test_offers_setter_accepts_none(self):
        offer = Offer(listing_id=10, sender_id=3, offered_price=25.0)
        listing = Listing(1, "t", "d", 1.0, offers=[offer])
        listing.offers = None
        self.assertEqual(listing.offers, [])

    def test_offers_setter_raises_when_not_list(self):
        listing = Listing(1, "t", "d", 1.0)
        with self.assertRaises(ValidationError):
            listing.offers = "bad"

    def test_offers_setter_raises_when_item_not_offer(self):
        listing = Listing(1, "t", "d", 1.0)
        with self.assertRaises(ValidationError):
            listing.offers = ["not-an-offer"]

    def test_add_offer_success(self):
        listing = Listing(1, "t", "d", 1.0, listing_id=10)
        offer = Offer(listing_id=10, sender_id=3, offered_price=25.0)
        listing.add_offer(offer)
        self.assertIs(listing.offers[-1], offer)

    def test_add_offer_raises_when_none(self):
        listing = Listing(1, "t", "d", 1.0, listing_id=10)
        with self.assertRaises(ValidationError):
            listing.add_offer(None)

    def test_add_offer_raises_when_not_offer(self):
        listing = Listing(1, "t", "d", 1.0, listing_id=10)
        with self.assertRaises(ValidationError):
            listing.add_offer("bad")

    def test_add_offer_raises_when_listing_id_mismatch(self):
        listing = Listing(1, "t", "d", 1.0, listing_id=10)
        offer = Offer(listing_id=999, sender_id=3, offered_price=25.0)
        with self.assertRaises(ValidationError):
            listing.add_offer(offer)

    def test_add_offer_skips_id_check_before_persistence(self):
        listing = Listing(1, "t", "d", 1.0)
        offer = Offer(listing_id=999, sender_id=3, offered_price=25.0)
        listing.add_offer(offer)
        self.assertEqual(len(listing.offers), 1)

    def test_repr_includes_offers(self):
        listing = Listing(1, "t", "d", 1.0, listing_id=10)
        self.assertIn("offers=", repr(listing))
