from datetime import datetime, timedelta
import os
from pathlib import Path
import sys
import types
import unittest

import pytest

# src/__init__.py imports load_dotenv from python-dotenv; tests only need domain models.
sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from src.domain_models import Account, Listing, Comment, VerificationToken
from src.utils import ValidationError, UnapprovedBehaviorError


class TestAccountDomainModel:
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

        assert account.id == 10
        assert account.email == "user@example.com"
        assert account.password == "hash"
        assert account.fname == "testFirst"
        assert account.lname == "testLast"
        assert account.verified is False

        account.email = "  next@example.com "
        account.password = " next-hash "
        account.fname = " First "
        account.lname = " Last "
        account.verified = True

        assert account.email == "next@example.com"
        assert account.password == "next-hash"
        assert account.fname == "First"
        assert account.lname == "Last"
        assert account.verified is True

        listed = account.listings
        listed.clear()
        assert len(account.listings) == 1

        rep = repr(account)
        assert "Account(id=10" in rep
        assert "listings_count=1" in rep

    def test_account_mark_persisted_success(self):
        account = Account("user@example.com", "hash", "First", "Last")
        account.mark_persisted(42)
        assert account.id == 42

    def test_account_mark_persisted_fails_for_none_and_double_assign(self):
        account = Account("user@example.com", "hash", "First", "Last")
        with pytest.raises(ValidationError):
            account.mark_persisted(None)

        account.mark_persisted(12)
        with pytest.raises(UnapprovedBehaviorError):
            account.mark_persisted(13)

    def test_account_verified_rejects_none(self):
        account = Account("user@example.com", "hash", "First", "Last")
        with pytest.raises(ValidationError):
            account.verified = None

    def test_account_add_and_remove_listing(self):
        account = Account("user@example.com", "hash", "First", "Last", account_id=1)
        listing = Listing(1, "Title", "Desc", 5.0, listing_id=7, comments=[])

        account.add_listing(listing)
        assert [l.id for l in account.listings] == [7]

        account.remove_listing(7)
        assert account.listings == []

    def test_account_add_listing_rejects_none_and_mismatched_seller(self):
        account = Account("user@example.com", "hash", "First", "Last", account_id=1)

        with pytest.raises(ValidationError):
            account.add_listing(None)

        with pytest.raises(UnapprovedBehaviorError):
            account.add_listing(Listing(2, "Title", "Desc", 5.0, listing_id=7, comments=[]))

    def test_account_remove_listing_rejects_unknown_id(self):
        account = Account("user@example.com", "hash", "First", "Last", account_id=1)
        with pytest.raises(ValidationError):
            account.remove_listing(999)


class TestCommentDomainModel:
    def test_comment_properties_mutators_repr_and_mark_persisted(self):
        created = datetime(2026, 1, 1, 12, 0, 0)
        comment = Comment(listing_id=5, author_id=7, body=" hello ", created_date=created)

        assert comment.id is None
        assert comment.listing_id == 5
        assert comment.author_id == 7
        assert comment.body == "hello"
        assert comment.created_date == created

        comment.listing_id = 6
        comment.author_id = 8
        comment.body = None
        assert comment.listing_id == 6
        assert comment.author_id == 8
        assert comment.body is None

        comment.mark_persisted(33)
        assert comment.id == 33

        rep = repr(comment)
        assert "Comment(id=33" in rep

    def test_comment_mark_persisted_rejects_none_and_double_assign(self):
        comment = Comment(listing_id=1, author_id=2)
        with pytest.raises(ValidationError):
            comment.mark_persisted(None)

        comment.mark_persisted(9)
        with pytest.raises(UnapprovedBehaviorError):
            comment.mark_persisted(10)


class TestListingDomainModel:
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

        assert listing.id is None
        assert listing.seller_id == 1
        assert listing.title == "title"
        assert listing.description == "desc"
        assert listing.price == 10.0
        assert listing.image_url == "image.jpg"
        assert listing.location == "Winnipeg"
        assert listing.created_at == "2026-01-01"
        assert listing.is_sold is False
        assert listing.sold_to_id is None
        assert listing.comments == []

        listing.mark_persisted(100)
        assert listing.id == 100

        listing.seller_id = 2
        listing.title = " New Title "
        listing.description = " New Desc "
        listing.image_url = None
        listing.image_url = " img2.png "
        listing.price = 25
        listing.location = None
        listing.location = " Campus "

        assert listing.seller_id == 2
        assert listing.title == "New Title"
        assert listing.description == "New Desc"
        assert listing.image_url == "img2.png"
        assert listing.price == 25.0
        assert listing.location == "Campus"

        rep = repr(listing)
        assert "Listing(id=100" in rep

    def test_listing_mark_persisted_rejects_none_and_double_assign(self):
        listing = Listing(1, "t", "d", 1.0, comments=[])
        with pytest.raises(ValidationError):
            listing.mark_persisted(None)

        listing.mark_persisted(1)
        with pytest.raises(UnapprovedBehaviorError):
            listing.mark_persisted(2)

    def test_listing_constructor_enforces_sold_invariants(self):
        with pytest.raises(ValidationError):
            Listing(1, "t", "d", 2.0, is_sold=True, sold_to_id=None, comments=[])

        with pytest.raises(ValidationError):
            Listing(1, "t", "d", 2.0, is_sold=False, sold_to_id=3, comments=[])

    def test_listing_mark_sold_success_and_double_sell(self):
        listing = Listing(1, "t", "d", 1.0, comments=[])
        listing.mark_sold(4)
        assert listing.is_sold is True
        assert listing.sold_to_id == 4.0

        with pytest.raises(UnapprovedBehaviorError):
            listing.mark_sold(5)

    def test_listing_comments_setter_none_invalid_type_invalid_item_and_copy(self):
        listing = Listing(1, "t", "d", 1.0, comments=[])

        listing.comments = None
        assert listing.comments is None

        with pytest.raises(ValidationError):
            listing.comments = "not-a-list"

        with pytest.raises(ValidationError):
            listing.comments = ["bad-item"]

        comment = Comment(1, 2, body="ok")
        original = [comment]
        listing.comments = original
        original.clear()
        assert len(listing.comments) == 1

    def test_listing_add_comment_and_add_comments_paths(self):
        listing = Listing(1, "t", "d", 1.0, listing_id=10, comments=[])
        c1 = Comment(10, 2, body="a")
        c2 = Comment(10, 3, body="b")

        with pytest.raises(ValidationError):
            listing.add_comment(None)

        listing.add_comment(c1)
        assert listing.comments[-1] is c1

        with pytest.raises(ValidationError):
            listing.add_comments(None)

        with pytest.raises(ValidationError):
            listing.add_comments("nope")

        with pytest.raises(ValidationError):
            listing.add_comments(["bad-item"])

        with pytest.raises(ValidationError):
            listing.add_comments([Comment(999, 2, body="wrong listing")])

        listing.add_comments([c2])
        assert listing.comments[-1] is c2


class TestVerificationTokenDomainModel:
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

        assert token.id is None
        assert token.account_id == 1
        assert token.token_hash == "hash"
        assert token.expires_at is not None
        assert token.created_at is not None
        assert token.used is False
        assert token.used_at is None

        token.mark_persisted(12)
        assert token.id == 12

        token.mark_as_used()
        assert token.used is True
        assert token.used_at is not None

        rep = repr(token)
        assert "VerificationToken(id=12" in rep

    def test_verification_token_mark_persisted_rejects_none_and_double_assign(self):
        token = VerificationToken(
            account_id=1,
            token_hash="hash",
            expires_at=datetime.now() + timedelta(minutes=5),
        )

        with pytest.raises(ValidationError):
            token.mark_persisted(None)

        token.mark_persisted(1)
        with pytest.raises(ValidationError):
            token.mark_persisted(2)

    def test_verification_token_mark_as_used_rejects_double_use(self):
        token = VerificationToken(
            account_id=1,
            token_hash="hash",
            expires_at=datetime.now() + timedelta(minutes=5),
            used=True,
        )

        with pytest.raises(ValidationError):
            token.mark_as_used()

    def test_verification_token_is_expired_and_is_valid_paths(self):
        expired = VerificationToken(
            account_id=1,
            token_hash="hash",
            expires_at=datetime.now() - timedelta(seconds=1),
        )
        assert expired.is_expired() is True
        assert expired.is_valid() is False

        valid = VerificationToken(
            account_id=1,
            token_hash="hash",
            expires_at=datetime.now() + timedelta(minutes=1),
            used=False,
        )
        assert valid.is_expired() is False
        assert valid.is_valid() is True

        used = VerificationToken(
            account_id=1,
            token_hash="hash",
            expires_at=datetime.now() + timedelta(minutes=1),
            used=True,
        )
        assert used.is_valid() is False


class TestDomainModels(unittest.TestCase):
    def test_account_properties_and_mutators_and_repr(self):
        TestAccountDomainModel().test_account_properties_and_mutators_and_repr()

    def test_account_mark_persisted_success(self):
        TestAccountDomainModel().test_account_mark_persisted_success()

    def test_account_mark_persisted_fails_for_none_and_double_assign(self):
        TestAccountDomainModel().test_account_mark_persisted_fails_for_none_and_double_assign()

    def test_account_verified_rejects_none(self):
        TestAccountDomainModel().test_account_verified_rejects_none()

    def test_account_add_and_remove_listing(self):
        TestAccountDomainModel().test_account_add_and_remove_listing()

    def test_account_add_listing_rejects_none_and_mismatched_seller(self):
        TestAccountDomainModel().test_account_add_listing_rejects_none_and_mismatched_seller()

    def test_account_remove_listing_rejects_unknown_id(self):
        TestAccountDomainModel().test_account_remove_listing_rejects_unknown_id()

    def test_comment_properties_mutators_repr_and_mark_persisted(self):
        TestCommentDomainModel().test_comment_properties_mutators_repr_and_mark_persisted()

    def test_comment_mark_persisted_rejects_none_and_double_assign(self):
        TestCommentDomainModel().test_comment_mark_persisted_rejects_none_and_double_assign()

    def test_listing_properties_mutators_mark_persisted_and_repr(self):
        TestListingDomainModel().test_listing_properties_mutators_mark_persisted_and_repr()

    def test_listing_mark_persisted_rejects_none_and_double_assign(self):
        TestListingDomainModel().test_listing_mark_persisted_rejects_none_and_double_assign()

    def test_listing_constructor_enforces_sold_invariants(self):
        TestListingDomainModel().test_listing_constructor_enforces_sold_invariants()

    def test_listing_mark_sold_success_and_double_sell(self):
        TestListingDomainModel().test_listing_mark_sold_success_and_double_sell()

    def test_listing_comments_setter_none_invalid_type_invalid_item_and_copy(self):
        TestListingDomainModel().test_listing_comments_setter_none_invalid_type_invalid_item_and_copy()

    def test_listing_add_comment_and_add_comments_paths(self):
        TestListingDomainModel().test_listing_add_comment_and_add_comments_paths()

    def test_verification_token_properties_repr_mark_persisted_and_mark_as_used(self):
        TestVerificationTokenDomainModel().test_verification_token_properties_repr_mark_persisted_and_mark_as_used()

    def test_verification_token_mark_persisted_rejects_none_and_double_assign(self):
        TestVerificationTokenDomainModel().test_verification_token_mark_persisted_rejects_none_and_double_assign()

    def test_verification_token_mark_as_used_rejects_double_use(self):
        TestVerificationTokenDomainModel().test_verification_token_mark_as_used_rejects_double_use()

    def test_verification_token_is_expired_and_is_valid_paths(self):
        TestVerificationTokenDomainModel().test_verification_token_is_expired_and_is_valid_paths()
