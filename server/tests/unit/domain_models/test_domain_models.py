from datetime import datetime, timedelta
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

from src.domain_models import Account, Listing, Comment, VerificationToken
from src.utils import ValidationError, UnapprovedBehaviorError


class TestDomainModels(unittest.TestCase):
    def test_account_properties_and_mutators_and_repr(self):
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

    def test_account_mark_persisted_success(self):
        account = Account("user@example.com", "hash", "First", "Last")
        account.mark_persisted(42)
        self.assertEqual(account.id, 42)

    def test_account_mark_persisted_fails_for_none_and_double_assign(self):
        account = Account("user@example.com", "hash", "First", "Last")
        with self.assertRaises(ValidationError):
            account.mark_persisted(None)

        account.mark_persisted(12)
        with self.assertRaises(UnapprovedBehaviorError):
            account.mark_persisted(13)

    def test_account_verified_rejects_none(self):
        account = Account("user@example.com", "hash", "First", "Last")
        with self.assertRaises(ValidationError):
            account.verified = None

    def test_account_add_and_remove_listing(self):
        account = Account("user@example.com", "hash", "First", "Last", account_id=1)
        listing = Listing(1, "Title", "Desc", 5.0, listing_id=7, comments=[])

        account.add_listing(listing)
        self.assertEqual([l.id for l in account.listings], [7])

        account.remove_listing(7)
        self.assertEqual(account.listings, [])

    def test_account_add_listing_rejects_none_and_mismatched_seller(self):
        account = Account("user@example.com", "hash", "First", "Last", account_id=1)

        with self.assertRaises(ValidationError):
            account.add_listing(None)

        with self.assertRaises(UnapprovedBehaviorError):
            account.add_listing(
                Listing(2, "Title", "Desc", 5.0, listing_id=7, comments=[])
            )

    def test_account_remove_listing_rejects_unknown_id(self):
        account = Account("user@example.com", "hash", "First", "Last", account_id=1)
        with self.assertRaises(ValidationError):
            account.remove_listing(999)

    def test_comment_properties_mutators_repr_and_mark_persisted(self):
        created = datetime(2026, 1, 1, 12, 0, 0)
        comment = Comment(
            listing_id=5, author_id=7, body=" hello ", created_date=created
        )

        self.assertIsNone(comment.id)
        self.assertEqual(comment.listing_id, 5)
        self.assertEqual(comment.author_id, 7)
        self.assertEqual(comment.body, "hello")
        self.assertEqual(comment.created_date, created)

        comment.listing_id = 6
        comment.author_id = 8
        comment.body = None
        self.assertEqual(comment.listing_id, 6)
        self.assertEqual(comment.author_id, 8)
        self.assertIsNone(comment.body)

        comment.mark_persisted(33)
        self.assertEqual(comment.id, 33)

        rep = repr(comment)
        self.assertIn("Comment(id=33", rep)

    def test_comment_mark_persisted_rejects_none_and_double_assign(self):
        comment = Comment(listing_id=1, author_id=2)
        with self.assertRaises(ValidationError):
            comment.mark_persisted(None)

        comment.mark_persisted(9)
        with self.assertRaises(UnapprovedBehaviorError):
            comment.mark_persisted(10)

    def test_listing_properties_mutators_mark_persisted_and_repr(self):
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

    def test_listing_mark_persisted_rejects_none_and_double_assign(self):
        listing = Listing(1, "t", "d", 1.0, comments=[])
        with self.assertRaises(ValidationError):
            listing.mark_persisted(None)

        listing.mark_persisted(1)
        with self.assertRaises(UnapprovedBehaviorError):
            listing.mark_persisted(2)

    def test_listing_constructor_enforces_sold_invariants(self):
        with self.assertRaises(ValidationError):
            Listing(1, "t", "d", 2.0, is_sold=True, sold_to_id=None, comments=[])

        with self.assertRaises(ValidationError):
            Listing(1, "t", "d", 2.0, is_sold=False, sold_to_id=3, comments=[])

    def test_listing_mark_sold_success_and_double_sell(self):
        listing = Listing(1, "t", "d", 1.0, comments=[])
        listing.mark_sold(4)
        self.assertTrue(listing.is_sold)
        self.assertEqual(listing.sold_to_id, 4.0)

        with self.assertRaises(UnapprovedBehaviorError):
            listing.mark_sold(5)

    def test_listing_comments_setter_none_invalid_type_invalid_item_and_copy(self):
        listing = Listing(1, "t", "d", 1.0, comments=[])

        listing.comments = None
        self.assertEqual(listing.comments, [])

        with self.assertRaises(ValidationError):
            listing.comments = "not-a-list"

        with self.assertRaises(ValidationError):
            listing.comments = ["bad-item"]

        comment = Comment(1, 2, body="ok")
        original = [comment]
        listing.comments = original
        original.clear()
        self.assertEqual(len(listing.comments), 1)

    def test_listing_add_comment_and_add_comments_paths(self):
        listing = Listing(1, "t", "d", 1.0, listing_id=10, comments=[])
        c1 = Comment(10, 2, body="a")
        c2 = Comment(10, 3, body="b")

        with self.assertRaises(ValidationError):
            listing.add_comment(None)

        listing.add_comment(c1)
        self.assertIs(listing.comments[-1], c1)

        with self.assertRaises(ValidationError):
            listing.add_comments(None)

        with self.assertRaises(ValidationError):
            listing.add_comments("nope")

        with self.assertRaises(ValidationError):
            listing.add_comments(["bad-item"])

        with self.assertRaises(ValidationError):
            listing.add_comments([Comment(999, 2, body="wrong listing")])

        listing.add_comments([c2])
        self.assertIs(listing.comments[-1], c2)

    def test_verification_token_properties_repr_mark_persisted_and_mark_as_used(self):
        now = datetime.now()
        token = VerificationToken(
            account_id=1,
            token_hash="hash",
            expires_at=now + timedelta(minutes=5),
            token_id=None,
            used=False,
            used_at=None,
        )

        self.assertIsNone(token.id)
        self.assertEqual(token.account_id, 1)
        self.assertEqual(token.token_hash, "hash")
        self.assertIsNotNone(token.expires_at)
        self.assertIsNotNone(token.created_at)
        self.assertFalse(token.used)
        self.assertIsNone(token.used_at)

        token.mark_persisted(12)
        self.assertEqual(token.id, 12)

        token.mark_as_used()
        self.assertTrue(token.used)
        self.assertIsNotNone(token.used_at)

        rep = repr(token)
        self.assertIn("VerificationToken(id=12", rep)

    def test_verification_token_mark_persisted_rejects_none_and_double_assign(self):
        token = VerificationToken(
            account_id=1,
            token_hash="hash",
            expires_at=datetime.now() + timedelta(minutes=5),
        )

        with self.assertRaises(ValidationError):
            token.mark_persisted(None)

        token.mark_persisted(1)
        with self.assertRaises(ValidationError):
            token.mark_persisted(2)

    def test_verification_token_mark_as_used_rejects_double_use(self):
        token = VerificationToken(
            account_id=1,
            token_hash="hash",
            expires_at=datetime.now() + timedelta(minutes=5),
            used=True,
        )

        with self.assertRaises(ValidationError):
            token.mark_as_used()

    def test_verification_token_is_expired_and_is_valid_paths(self):
        expired = VerificationToken(
            account_id=1,
            token_hash="hash",
            expires_at=datetime.now() - timedelta(seconds=1),
        )
        self.assertTrue(expired.is_expired())
        self.assertFalse(expired.is_valid())

        valid = VerificationToken(
            account_id=1,
            token_hash="hash",
            expires_at=datetime.now() + timedelta(minutes=1),
            used=False,
        )
        self.assertFalse(valid.is_expired())
        self.assertTrue(valid.is_valid())

        used = VerificationToken(
            account_id=1,
            token_hash="hash",
            expires_at=datetime.now() + timedelta(minutes=1),
            used=True,
        )
        self.assertFalse(used.is_valid())

    def test_account_remove_listing_success_removes_when_present(self):
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

        self.assertEqual([l.id for l in account.listings], [11, 22])

        account.remove_listing(11)

        self.assertEqual([l.id for l in account.listings], [22])

    def test_account_remove_listing_invalid_or_missing_raises(self):
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
