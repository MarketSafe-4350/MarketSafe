from __future__ import annotations

import unittest
from unittest.mock import Mock

from src.business_logic.managers.comment import CommentManager
from src.domain_models import Account, Listing, Comment
from src.utils import (
    ValidationError,
    UnapprovedBehaviorError,
    CommentNotFoundError,
)


class TestCommentManagerUnit(unittest.TestCase):
    def setUp(self) -> None:
        self.comment_db = Mock()
        self.mgr = CommentManager(self.comment_db)

    # -----------------------------
    # helpers
    # -----------------------------
    def _account(self, account_id: int, *, verified: bool = True) -> Account:
        return Account(
            email=f"user{account_id}@example.com",
            password="pass",
            fname="A",
            lname="B",
            verified=verified,
            account_id=account_id,
        )

    def _listing(
        self,
        *,
        listing_id: int | None,
        seller_id: int,
        is_sold: bool = False,
        sold_to_id: int | None = None,
    ) -> Listing:
        if is_sold and sold_to_id is None:
            sold_to_id = 999  # any positive int
        if (not is_sold) and sold_to_id is not None:
            sold_to_id = None

        return Listing(
            seller_id=seller_id,
            title="t",
            description="d",
            price=10.0,
            listing_id=listing_id,
            is_sold=is_sold,
            sold_to_id=sold_to_id,
            location="Winnipeg",
        )

    def _comment(
        self,
        *,
        comment_id: int | None,
        listing_id: int,
        author_id: int,
        body: str | None = "none",
    ) -> Comment:
        return Comment(
            listing_id=listing_id,
            author_id=author_id,
            body=body,
            comment_id=comment_id,
        )

    # -----------------------------
    # CREATE
    # -----------------------------
    def test_create_comment_requires_persisted_actor(self) -> None:
        actor = self._account(1, verified=True)
        # simulate non-persisted actor
        actor._id = None 

        listing = self._listing(listing_id=10, seller_id=2, is_sold=False)
        comment = self._comment(comment_id=None, listing_id=10, author_id=1, body="x")

        with self.assertRaises(ValidationError):
            self.mgr.create_comment(actor=actor, listing=listing, comment=comment)

        self.comment_db.add.assert_not_called()

    def test_create_comment_requires_persisted_listing(self) -> None:
        actor = self._account(1, verified=True)
        listing = self._listing(listing_id=None, seller_id=2, is_sold=False)
        comment = self._comment(comment_id=None, listing_id=999, author_id=1, body="x")

        with self.assertRaises(ValidationError):
            self.mgr.create_comment(actor=actor, listing=listing, comment=comment)

        self.comment_db.add.assert_not_called()

    def test_create_comment_requires_new_comment(self) -> None:
        actor = self._account(1, verified=True)
        listing = self._listing(listing_id=10, seller_id=2, is_sold=False)
        comment = self._comment(comment_id=55, listing_id=10, author_id=1, body="x")

        with self.assertRaises(ValidationError):
            self.mgr.create_comment(actor=actor, listing=listing, comment=comment)

        self.comment_db.add.assert_not_called()

    def test_create_comment_rejects_author_spoofing(self) -> None:
        actor = self._account(1, verified=True)
        listing = self._listing(listing_id=10, seller_id=2, is_sold=False)
        comment = self._comment(comment_id=None, listing_id=10, author_id=999, body="x")

        with self.assertRaises(UnapprovedBehaviorError):
            self.mgr.create_comment(actor=actor, listing=listing, comment=comment)

        self.comment_db.add.assert_not_called()

    def test_create_comment_requires_matching_listing_id(self) -> None:
        actor = self._account(1, verified=True)
        listing = self._listing(listing_id=10, seller_id=2, is_sold=False)
        comment = self._comment(comment_id=None, listing_id=999, author_id=1, body="x")

        with self.assertRaises(ValidationError):
            self.mgr.create_comment(actor=actor, listing=listing, comment=comment)

        self.comment_db.add.assert_not_called()

    def test_create_comment_requires_verified_actor(self) -> None:
        actor = self._account(1, verified=False)
        listing = self._listing(listing_id=10, seller_id=2, is_sold=False)
        comment = self._comment(comment_id=None, listing_id=10, author_id=1, body="x")

        with self.assertRaises(UnapprovedBehaviorError):
            self.mgr.create_comment(actor=actor, listing=listing, comment=comment)

        self.comment_db.add.assert_not_called()

    def test_create_comment_rejects_sold_listing(self) -> None:
        actor = self._account(1, verified=True)
        listing = self._listing(listing_id=10, seller_id=2, is_sold=True, sold_to_id=3)
        comment = self._comment(comment_id=None, listing_id=10, author_id=1, body="x")

        with self.assertRaises(UnapprovedBehaviorError):
            self.mgr.create_comment(actor=actor, listing=listing, comment=comment)

        self.comment_db.add.assert_not_called()

    def test_create_comment_happy_path_calls_db(self) -> None:
        actor = self._account(1, verified=True)
        listing = self._listing(listing_id=10, seller_id=2, is_sold=False)
        comment = self._comment(comment_id=None, listing_id=10, author_id=1, body="hello")

        created = self._comment(comment_id=99, listing_id=10, author_id=1, body="hello")
        self.comment_db.add.return_value = created

        out = self.mgr.create_comment(actor=actor, listing=listing, comment=comment)

        self.assertEqual(out, created)
        self.comment_db.add.assert_called_once_with(comment)

    # -----------------------------
    # READ
    # -----------------------------
    def test_get_comment_by_id_pass_through(self) -> None:
        comment = self._comment(comment_id=1, listing_id=10, author_id=2, body="x")
        self.comment_db.get_by_id.return_value = comment

        out = self.mgr.get_comment_by_id(1)

        self.assertEqual(out, comment)
        self.comment_db.get_by_id.assert_called_once_with(1)

    def test_list_comments_for_listing_pass_through(self) -> None:
        self.comment_db.get_by_listing_id.return_value = []

        out = self.mgr.list_comments_for_listing(10)

        self.assertEqual(out, [])
        self.comment_db.get_by_listing_id.assert_called_once_with(10)

    def test_list_comments_for_author_pass_through(self) -> None:
        self.comment_db.get_by_author_id.return_value = []

        out = self.mgr.list_comments_for_author(5)

        self.assertEqual(out, [])
        self.comment_db.get_by_author_id.assert_called_once_with(5)

    # -----------------------------
    # UPDATE
    # -----------------------------
    def test_update_comment_body_requires_persisted_actor(self) -> None:
        actor = self._account(1, verified=True)
        actor._id = None 

        comment = self._comment(comment_id=5, listing_id=10, author_id=1, body="new")

        with self.assertRaises(ValidationError):
            self.mgr.update_comment_body(actor=actor, comment=comment)

        self.comment_db.update_body.assert_not_called()

    def test_update_comment_body_requires_persisted_comment(self) -> None:
        actor = self._account(1, verified=True)
        comment = self._comment(comment_id=None, listing_id=10, author_id=1, body="new")

        with self.assertRaises(ValidationError):
            self.mgr.update_comment_body(actor=actor, comment=comment)

        self.comment_db.update_body.assert_not_called()

    def test_update_comment_body_requires_verified_actor(self) -> None:
        actor = self._account(1, verified=False)
        comment = self._comment(comment_id=5, listing_id=10, author_id=1, body="new")

        with self.assertRaises(UnapprovedBehaviorError):
            self.mgr.update_comment_body(actor=actor, comment=comment)

        self.comment_db.update_body.assert_not_called()

    def test_update_comment_body_only_author_can_edit(self) -> None:
        actor = self._account(1, verified=True)
        comment = self._comment(comment_id=5, listing_id=10, author_id=999, body="new")

        with self.assertRaises(UnapprovedBehaviorError):
            self.mgr.update_comment_body(actor=actor, comment=comment)

        self.comment_db.update_body.assert_not_called()

    def test_update_comment_body_raises_when_missing_after_update(self) -> None:
        actor = self._account(1, verified=True)
        comment = self._comment(comment_id=5, listing_id=10, author_id=1, body="new")

        # update happens, then refreshed fetch returns None -> NotFound
        self.comment_db.get_by_id.return_value = None

        with self.assertRaises(CommentNotFoundError):
            self.mgr.update_comment_body(actor=actor, comment=comment)

        self.comment_db.update_body.assert_called_once_with(5, "new")
        self.comment_db.get_by_id.assert_called_once_with(5)

    def test_update_comment_body_happy_path_returns_refreshed(self) -> None:
        actor = self._account(1, verified=True)
        comment = self._comment(comment_id=5, listing_id=10, author_id=1, body="new")

        refreshed = self._comment(comment_id=5, listing_id=10, author_id=1, body="new")
        self.comment_db.get_by_id.return_value = refreshed

        out = self.mgr.update_comment_body(actor=actor, comment=comment)

        self.comment_db.update_body.assert_called_once_with(5, "new")
        self.comment_db.get_by_id.assert_called_once_with(5)
        self.assertEqual(out, refreshed)

    # -----------------------------
    # DELETE
    # -----------------------------
    def test_delete_comment_returns_false_when_missing(self) -> None:
        actor = self._account(1, verified=True)
        self.comment_db.get_by_id.return_value = None

        out = self.mgr.delete_comment(actor=actor, comment_id=123)

        self.assertFalse(out)
        self.comment_db.get_by_id.assert_called_once_with(123)
        self.comment_db.remove.assert_not_called()

    def test_delete_comment_requires_persisted_actor(self) -> None:
        actor = self._account(account_id=None)
        
        with self.assertRaises(ValidationError):
            self.mgr.delete_comment(actor=actor, comment_id=123)
        
        self.comment_db.get_by_id.assert_not_called()
        self.comment_db.remove.assert_not_called()

    def test_delete_comment_requires_verified_actor(self) -> None:
        actor = self._account(1, verified=False)

        with self.assertRaises(UnapprovedBehaviorError):
            self.mgr.delete_comment(actor=actor, comment_id=123)

        self.comment_db.get_by_id.assert_not_called()
        self.comment_db.remove.assert_not_called()

    def test_delete_comment_only_author_can_delete(self) -> None:
        actor = self._account(1, verified=True)
        existing = self._comment(comment_id=123, listing_id=10, author_id=999, body="x")
        self.comment_db.get_by_id.return_value = existing

        with self.assertRaises(UnapprovedBehaviorError):
            self.mgr.delete_comment(actor=actor, comment_id=123)

        self.comment_db.remove.assert_not_called()

    def test_delete_comment_happy_path_calls_db(self) -> None:
        actor = self._account(1, verified=True)
        existing = self._comment(comment_id=123, listing_id=10, author_id=1, body="x")
        self.comment_db.get_by_id.return_value = existing
        self.comment_db.remove.return_value = True

        out = self.mgr.delete_comment(actor=actor, comment_id=123)

        self.assertTrue(out)
        self.comment_db.remove.assert_called_once_with(123)
