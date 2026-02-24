from __future__ import annotations

import unittest
from uuid import uuid4
from typing import List

from src.business_logic.managers.comment.comment_manager import CommentManager
from src.db.account.mysql import MySQLAccountDB
from src.db.listing.mysql.mysql_listing_db import MySQLListingDB
from src.db.comment.mysql.mysql_comment_db import MySQLCommentDB

from src.domain_models import Listing, Comment, Account

from src.utils import (
    ValidationError,
    UnapprovedBehaviorError,
    CommentNotFoundError,
)

from tests.helpers.integration_db import ensure_tables_exist, reset_all_tables
from tests.helpers.integration_db_session import acquire, get_db, release


class TestCommentManagerIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:

        cls._session = acquire(timeout_s=60)
        cls._db = get_db()

        ensure_tables_exist(cls._db, timeout_s=60)
        reset_all_tables(cls._db)


        cls._account_db = MySQLAccountDB(cls._db)
        cls._listing_db = MySQLListingDB(cls._db)
        cls._comment_db = MySQLCommentDB(cls._db)
        cls._mgr = CommentManager(cls._comment_db)

    @classmethod
    def setUp(cls) -> None:
        # Keep tests independent
        reset_all_tables(cls._db)

    @classmethod
    def tearDownClass(cls) -> None:
        release(cls._session, remove_volumes=False)


    # -----------------------------
    # helpers
    # -----------------------------
    def _new_account(self, prefix: str = "user", *, verified: bool = False) -> Account:
        uniq = uuid4().hex[:10]
        return Account(
            email=f"{prefix}_{uniq}@example.com",
            password="pass",
            fname="Test",
            lname="User",
            verified=verified,
        )

    def _create_account(self, prefix: str = "user", *, verified: bool = False) -> Account:
        created = self._account_db.add(self._new_account(prefix, verified=verified))
        self.assertIsNotNone(created.id)
        return created

    def _new_listing(
        self, seller_id: int, *, title: str | None = None, price: float = 123.45, is_sold: bool = False
    ) -> Listing:
        uniq = uuid4().hex[:10]
        return Listing(
            seller_id=seller_id,
            title=title or f"Title {uniq}",
            description=f"Desc {uniq}",
            price=price,
            location="Winnipeg",
            is_sold=is_sold,
            sold_to_id=None,
        )

    def _create_listing(self, seller: Account, *, is_sold: bool = False) -> Listing:
        created = self._listing_db.add(self._new_listing(seller.id, is_sold=is_sold))
        self.assertIsNotNone(created.id)
        return created

    def _new_comment(self, listing_id: int, author_id: int, *, body: str | None = "hello") -> Comment:
        return Comment(
            listing_id=listing_id,
            author_id=author_id,
            body=body,
            comment_id=None,
        )

    # -----------------------------
    # CREATE
    # -----------------------------
    def test_create_comment_happy_path(self) -> None:
        seller = self._create_account("seller", verified=False)
        listing = self._create_listing(seller)

        actor = self._create_account("actor", verified=True)
        comment = self._new_comment(listing.id, actor.id, body="first!")

        created = self._mgr.create_comment(actor=actor, listing=listing, comment=comment)

        self.assertIsNotNone(created.id)
        self.assertEqual(created.listing_id, listing.id)
        self.assertEqual(created.author_id, actor.id)
        self.assertEqual(created.body, "first!")

        fetched = self._mgr.get_comment_by_id(created.id)
        self.assertIsNotNone(fetched)

    def test_create_comment_requires_verified_actor(self) -> None:
        seller = self._create_account("seller")
        listing = self._create_listing(seller)

        actor = self._create_account("actor", verified=False)
        comment = self._new_comment(listing.id, actor.id, body="nope")

        with self.assertRaises(UnapprovedBehaviorError):
            self._mgr.create_comment(actor=actor, listing=listing, comment=comment)

    def test_create_comment_rejects_sold_listing(self) -> None:
        seller = self._create_account("seller")
        listing = self._create_listing(seller)

        # mark sold in DB
        buyer = self._create_account("buyer")
        self._listing_db.set_sold(listing.id, True, buyer.id)

        sold_listing = self._listing_db.get_by_id(listing.id)
        self.assertIsNotNone(sold_listing)
        assert sold_listing is not None
        self.assertTrue(bool(sold_listing.is_sold))

        actor = self._create_account("actor", verified=True)
        comment = self._new_comment(sold_listing.id, actor.id, body="should fail")

        with self.assertRaises(UnapprovedBehaviorError):
            self._mgr.create_comment(actor=actor, listing=sold_listing, comment=comment)

    def test_create_comment_requires_persisted_actor_and_listing(self) -> None:
        seller = self._create_account("seller")
        created_listing = self._create_listing(seller)

        actor = self._new_account("actor", verified=True) 
        comment = self._new_comment(created_listing.id, author_id=999, body="x") 

        with self.assertRaises(ValidationError):
            self._mgr.create_comment(actor=actor, listing=created_listing, comment=comment)

        actor2 = self._create_account("actor2", verified=True)
        not_persisted_listing = self._new_listing(seller_id=seller.id) 
        comment2 = self._new_comment(listing_id=999, author_id=actor2.id, body="x")

        with self.assertRaises(ValidationError):
            self._mgr.create_comment(actor=actor2, listing=not_persisted_listing, comment=comment2)

    def test_create_comment_rejects_comment_on_behalf_of_other_user(self) -> None:
        seller = self._create_account("seller")
        listing = self._create_listing(seller)

        actor = self._create_account("actor", verified=True)
        other = self._create_account("other", verified=True)

        comment = self._new_comment(listing.id, other.id, body="bad")

        with self.assertRaises(UnapprovedBehaviorError):
            self._mgr.create_comment(actor=actor, listing=listing, comment=comment)

    # -----------------------------
    # READ
    # -----------------------------
    def test_list_comments_for_listing_and_author(self) -> None:
        seller = self._create_account("seller")
        listing = self._create_listing(seller)

        author = self._create_account("author", verified=True)
        c1 = self._mgr.create_comment(author, listing, self._new_comment(listing.id, author.id, body="a"))
        c2 = self._mgr.create_comment(author, listing, self._new_comment(listing.id, author.id, body="b"))

        by_listing = self._mgr.list_comments_for_listing(listing.id)
        self.assertEqual({x.id for x in by_listing}, {c1.id, c2.id})

        by_author = self._mgr.list_comments_for_author(author.id)
        self.assertEqual({x.id for x in by_author}, {c1.id, c2.id})

    # -----------------------------
    # UPDATE
    # -----------------------------
    def test_update_comment_body_happy_path(self) -> None:
        seller = self._create_account("seller")
        listing = self._create_listing(seller)

        actor = self._create_account("actor", verified=True)
        created = self._mgr.create_comment(actor, listing, self._new_comment(listing.id, actor.id, body="old"))

        updated_input = Comment(
            listing_id=created.listing_id,
            author_id=created.author_id,
            body="new",
            comment_id=created.id,
        )

        updated = self._mgr.update_comment_body(actor=actor, comment=updated_input)

        self.assertEqual(updated.id, created.id)
        self.assertEqual(updated.body, "new")

    def test_update_comment_body_requires_verified_actor(self) -> None:
        seller = self._create_account("seller")
        listing = self._create_listing(seller)

        author = self._create_account("author", verified=True)
        created = self._mgr.create_comment(author, listing, self._new_comment(listing.id, author.id, body="old"))

        not_verified = self._create_account("nv", verified=False)
        updated_input = Comment(
            listing_id=created.listing_id,
            author_id=created.author_id,
            body="new",
            comment_id=created.id,
        )

        with self.assertRaises(UnapprovedBehaviorError):
            self._mgr.update_comment_body(actor=not_verified, comment=updated_input)

    def test_update_comment_body_only_author_can_edit(self) -> None:
        seller = self._create_account("seller")
        listing = self._create_listing(seller)

        author = self._create_account("author", verified=True)
        created = self._mgr.create_comment(author, listing, self._new_comment(listing.id, author.id, body="old"))

        other = self._create_account("other", verified=True)
        updated_input = Comment(
            listing_id=created.listing_id,
            author_id=created.author_id,
            body="new",
            comment_id=created.id,
        )

        with self.assertRaises(UnapprovedBehaviorError):
            self._mgr.update_comment_body(actor=other, comment=updated_input)

    def test_update_comment_body_missing_comment_raises(self) -> None:
        actor = self._create_account("actor", verified=True)

        missing = Comment(
            listing_id=1,
            author_id=actor.id,
            body="x",
            comment_id=999999999,
        )

        with self.assertRaises(CommentNotFoundError):
            self._mgr.update_comment_body(actor=actor, comment=missing)

    # -----------------------------
    # DELETE
    # -----------------------------
    def test_delete_comment_happy_path(self) -> None:
        seller = self._create_account("seller")
        listing = self._create_listing(seller)

        actor = self._create_account("actor", verified=True)
        created = self._mgr.create_comment(actor, listing, self._new_comment(listing.id, actor.id, body="bye"))

        deleted = self._mgr.delete_comment(actor=actor, comment_id=created.id)
        self.assertTrue(deleted)

        # deleting again returns False
        deleted_again = self._mgr.delete_comment(actor=actor, comment_id=created.id)
        self.assertFalse(deleted_again)

    def test_delete_comment_requires_verified_actor(self) -> None:
        seller = self._create_account("seller")
        listing = self._create_listing(seller)

        author = self._create_account("author", verified=True)
        created = self._mgr.create_comment(author, listing, self._new_comment(listing.id, author.id, body="bye"))

        not_verified = self._create_account("nv", verified=False)

        with self.assertRaises(UnapprovedBehaviorError):
            self._mgr.delete_comment(actor=not_verified, comment_id=created.id)

    def test_delete_comment_only_author_can_delete(self) -> None:
        seller = self._create_account("seller")
        listing = self._create_listing(seller)

        author = self._create_account("author", verified=True)
        created = self._mgr.create_comment(author, listing, self._new_comment(listing.id, author.id, body="bye"))

        other = self._create_account("other", verified=True)

        with self.assertRaises(UnapprovedBehaviorError):
            self._mgr.delete_comment(actor=other, comment_id=created.id)