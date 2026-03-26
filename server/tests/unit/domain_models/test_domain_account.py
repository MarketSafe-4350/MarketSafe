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

from src.domain_models import Account, Listing
from src.utils import ValidationError, UnapprovedBehaviorError


class TestAccount(unittest.TestCase):

    # ==============================
    # properties, mutators, repr
    # ==============================

    def test_properties_mutators_and_repr(self):
        listing = Listing(10, "Title", "Desc", 9.99, listing_id=101, comments=[])
        account = Account(
            email="  USER@EXAMPLE.COM ",
            password="hash",
            fname=" testFirst ",
            lname=" testLast ",
            account_id=10,
            verified=False,
            listings=[listing],
        )

        self.assertEqual(account.id, 10)
        self.assertEqual(account.email, "user@example.com")
        self.assertEqual(account.password, "hash")
        self.assertEqual(account.fname, "testFirst")
        self.assertEqual(account.lname, "testLast")
        self.assertFalse(account.verified)

        account.email = "  next@example.com "
        account.password = " next-hash "
        account.fname = " First "
        account.lname = " Last "
        account.verified = True

        self.assertEqual(account.email, "next@example.com")
        self.assertEqual(account.password, "next-hash")
        self.assertEqual(account.fname, "First")
        self.assertEqual(account.lname, "Last")
        self.assertTrue(account.verified)

        listed = account.listings
        listed.clear()
        self.assertEqual(len(account.listings), 1)

        rep = repr(account)
        self.assertIn("Account(id=10", rep)
        self.assertIn("listings_count=1", rep)

    def test_verified_rejects_none(self):
        account = Account("user@example.com", "hash", "First", "Last")
        with self.assertRaises(ValidationError):
            account.verified = None

    # ==============================
    # mark_persisted
    # ==============================

    def test_mark_persisted_success(self):
        account = Account("user@example.com", "hash", "First", "Last")
        account.mark_persisted(42)
        self.assertEqual(account.id, 42)

    def test_mark_persisted_raises_when_none(self):
        account = Account("user@example.com", "hash", "First", "Last")
        with self.assertRaises(ValidationError):
            account.mark_persisted(None)

    def test_mark_persisted_raises_when_already_assigned(self):
        account = Account("user@example.com", "hash", "First", "Last")
        account.mark_persisted(12)
        with self.assertRaises(UnapprovedBehaviorError):
            account.mark_persisted(13)

    # ==============================
    # add_listing / remove_listing
    # ==============================

    def test_add_and_remove_listing(self):
        account = Account("user@example.com", "hash", "First", "Last", account_id=1)
        listing = Listing(1, "Title", "Desc", 5.0, listing_id=7, comments=[])

        account.add_listing(listing)
        self.assertEqual([l.id for l in account.listings], [7])

        account.remove_listing(7)
        self.assertEqual(account.listings, [])

    def test_add_listing_rejects_none(self):
        account = Account("user@example.com", "hash", "First", "Last", account_id=1)
        with self.assertRaises(ValidationError):
            account.add_listing(None)

    def test_add_listing_rejects_mismatched_seller(self):
        account = Account("user@example.com", "hash", "First", "Last", account_id=1)
        with self.assertRaises(UnapprovedBehaviorError):
            account.add_listing(
                Listing(2, "Title", "Desc", 5.0, listing_id=7, comments=[])
            )

    def test_remove_listing_rejects_unknown_id(self):
        account = Account("user@example.com", "hash", "First", "Last", account_id=1)
        with self.assertRaises(ValidationError):
            account.remove_listing(999)

    def test_remove_listing_removes_correct_entry(self):
        listing1 = Listing(1, "T1", "D1", 5.0, listing_id=11, comments=[])
        listing2 = Listing(1, "T2", "D2", 6.0, listing_id=22, comments=[])
        account = Account(
            email="user@example.com",
            password="hash",
            fname="First",
            lname="Last",
            account_id=1,
            listings=[listing1, listing2],
        )

        account.remove_listing(11)

        self.assertEqual([l.id for l in account.listings], [22])

    def test_remove_listing_raises_when_invalid_or_missing(self):
        listing = Listing(1, "T", "D", 5.0, listing_id=11, comments=[])
        account = Account(
            email="user@example.com",
            password="hash",
            fname="First",
            lname="Last",
            account_id=1,
            listings=[listing],
        )

        with self.assertRaises(ValidationError):
            account.remove_listing(0)

        with self.assertRaises(ValidationError) as ctx:
            account.remove_listing(999)

        self.assertIn("not found in this account", str(ctx.exception).lower())

    # ==============================
    # rating fields
    # ==============================

    def test_rating_fields_init_getters_and_setters(self):
        account = Account(
            email="user@example.com",
            password="hash",
            fname="First",
            lname="Last",
            average_rating_received=4.5,
            sum_of_ratings_received=7,
        )

        self.assertEqual(account.average_rating_received, 4.5)
        self.assertEqual(account.sum_of_ratings_received, 7)

        account.average_rating_received = 3.8
        account.sum_of_ratings_received = 9

        self.assertEqual(account.average_rating_received, 3.8)
        self.assertEqual(account.sum_of_ratings_received, 9)

    def test_average_rating_received_accepts_none(self):
        account = Account("user@example.com", "hash", "First", "Last")
        account.average_rating_received = None
        self.assertIsNone(account.average_rating_received)

    def test_average_rating_received_raises_when_negative(self):
        account = Account("user@example.com", "hash", "First", "Last")
        with self.assertRaises(ValidationError):
            account.average_rating_received = -1

    def test_sum_of_ratings_received_raises_when_negative(self):
        account = Account("user@example.com", "hash", "First", "Last")
        with self.assertRaises(ValidationError):
            account.sum_of_ratings_received = -1

    def test_rating_count_getter_returns_value(self):
        account = Account(
            email="user@example.com",
            password="hash",
            fname="First",
            lname="Last",
            rating_count=3,
        )
        self.assertEqual(account.rating_count, 3)

    def test_init_rejects_invalid_rating_fields(self):
        with self.assertRaises(ValidationError):
            Account(
                email="user@example.com",
                password="hash",
                fname="First",
                lname="Last",
                average_rating_received=-1,
            )

        with self.assertRaises(ValidationError):
            Account(
                email="user@example.com",
                password="hash",
                fname="First",
                lname="Last",
                sum_of_ratings_received=-1,
            )
