import unittest
from unittest.mock import MagicMock
from typing import List
from types import SimpleNamespace

from src.business_logic.services.comment_service import (
    CommentService,
    CommentWithAuthor,
)


class TestCommentServiceUnit(unittest.TestCase):
    def setUp(self) -> None:
        self.comment_manager: MagicMock = MagicMock()
        self.listing_manager: MagicMock = MagicMock()
        self.account_manager: MagicMock = MagicMock()

        self.service = CommentService(
            comment_manager=self.comment_manager,
            listing_manager=self.listing_manager,
            account_manager=self.account_manager,
        )

    # -----------------------------
    # get_all_comments_listing - happy path
    # -----------------------------
    def test_get_all_comments_listing_wraps_with_authors(self) -> None:
        listing_id = 123

        c1 = SimpleNamespace(id=1, listing_id=listing_id, author_id=999, body="hi")
        c2 = SimpleNamespace(id=2, listing_id=listing_id, author_id=888, body="yo")

        self.comment_manager.list_comments_for_listing.return_value = [c1, c2]

        a1 = SimpleNamespace(id=999, fname="A", lname="One", verified=True)
        a2 = SimpleNamespace(id=888, fname="B", lname="Two", verified=True)

        def fake_get_account_by_id(*, account_id: int):
            return {999: a1, 888: a2}[account_id]

        self.account_manager.get_account_by_id.side_effect = fake_get_account_by_id

        result = self.service.get_all_comments_listing(listing_id=listing_id)

        self.comment_manager.list_comments_for_listing.assert_called_once_with(
            listing_id=listing_id
        )

        self.assertEqual(len(result), 2)

        self.assertIsInstance(result[0], CommentWithAuthor)
        self.assertEqual(result[0].comment, c1)
        self.assertEqual(result[0].author, a1)

        self.assertIsInstance(result[1], CommentWithAuthor)
        self.assertEqual(result[1].comment, c2)
        self.assertEqual(result[1].author, a2)

        self.listing_manager.get_listing_by_id.assert_not_called()
        self.comment_manager.create_comment.assert_not_called()

    # -----------------------------
    # create_comment - happy path
    # -----------------------------
    def test_create_comment_returns_comment_with_author(self) -> None:
        actor_id = 999
        listing_id = 123

        actor = SimpleNamespace(id=actor_id, fname="F", lname="L", verified=True)
        listing = SimpleNamespace(id=listing_id, is_sold=False)

        comment = SimpleNamespace(
            id=None,
            listing_id=listing_id,
            author_id=actor_id,
            body="Is this available?",
        )

        created_comment = SimpleNamespace(
            id=10,
            listing_id=listing_id,
            author_id=actor_id,
            body="Is this available?",
            created_date=None,
        )

        self.account_manager.get_account_by_id.return_value = actor
        self.listing_manager.get_listing_by_id.return_value = listing
        self.comment_manager.create_comment.return_value = created_comment

        result = self.service.create_comment(
            actor_id=actor_id,
            listing_id=listing_id,
            comment=comment,
        )

        self.account_manager.get_account_by_id.assert_called_once_with(
            account_id=actor_id
        )
        self.listing_manager.get_listing_by_id.assert_called_once_with(
            listing_id=listing_id
        )
        self.comment_manager.create_comment.assert_called_once_with(
            actor=actor,
            listing=listing,
            comment=comment,
        )

        self.assertIsInstance(result, CommentWithAuthor)
        self.assertEqual(result.comment, created_comment)
        self.assertEqual(result.author, actor)
        self.assertEqual(result.comment.id, 10)

    # -----------------------------
    # create_comment - error paths
    # -----------------------------
    def test_create_comment_actor_lookup_error_propagates_and_stops(self) -> None:
        actor_id = 999
        listing_id = 123
        comment = SimpleNamespace(
            id=None, listing_id=listing_id, author_id=actor_id, body="x"
        )

        self.account_manager.get_account_by_id.side_effect = Exception("actor missing")

        with self.assertRaises(Exception) as ctx:
            self.service.create_comment(
                actor_id=actor_id, listing_id=listing_id, comment=comment
            )

        self.assertIn("actor missing", str(ctx.exception))

        self.listing_manager.get_listing_by_id.assert_not_called()
        self.comment_manager.create_comment.assert_not_called()

    def test_create_comment_listing_lookup_error_propagates_and_stops(self) -> None:
        actor_id = 999
        listing_id = 123
        actor = SimpleNamespace(id=actor_id, verified=True)
        comment = SimpleNamespace(
            id=None, listing_id=listing_id, author_id=actor_id, body="x"
        )

        self.account_manager.get_account_by_id.return_value = actor
        self.listing_manager.get_listing_by_id.side_effect = Exception(
            "listing missing"
        )

        with self.assertRaises(Exception) as ctx:
            self.service.create_comment(
                actor_id=actor_id, listing_id=listing_id, comment=comment
            )

        self.assertIn("listing missing", str(ctx.exception))

        self.comment_manager.create_comment.assert_not_called()
