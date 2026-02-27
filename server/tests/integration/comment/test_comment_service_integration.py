import unittest
from unittest.mock import MagicMock
from typing import List
from types import SimpleNamespace

from src.business_logic.services.comment_service import CommentService


class TestCommentServiceIntegration(unittest.TestCase):
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
    def test_get_all_comments_listing_delegates_to_manager(self) -> None:
        listing_id = 123

        expected_result: List[object] = [
            SimpleNamespace(id=1, listing_id=listing_id, author_id=999, body="Hi"),
            SimpleNamespace(id=2, listing_id=listing_id, author_id=888, body="Hello"),
        ]

        self.comment_manager.list_comments_for_listing.return_value = expected_result

        result = self.service.get_all_comments_listing(listing_id=listing_id)

        self.comment_manager.list_comments_for_listing.assert_called_once_with(
            listing_id=listing_id
        )
        self.assertEqual(result, expected_result)

        self.account_manager.get_account_by_id.assert_not_called()
        self.listing_manager.get_listing_by_id.assert_not_called()
        self.comment_manager.create_comment.assert_not_called()

    # -----------------------------
    # create_comment - happy path
    # -----------------------------
    def test_create_comment_loads_actor_and_listing_then_delegates_to_manager(
        self,
    ) -> None:
        actor_id = 999
        listing_id = 321

        actor = SimpleNamespace(id=actor_id, verified=True)
        listing = SimpleNamespace(id=listing_id, is_sold=False)

        comment = SimpleNamespace(
            id=None,
            listing_id=listing_id,
            author_id=actor_id,
            body="Is this still available?",
            created_date=None,
        )

        expected_result = SimpleNamespace(
            id=10,
            listing_id=listing_id,
            author_id=actor_id,
            body="Is this still available?",
            created_date=None,
        )

        self.account_manager.get_account_by_id.return_value = actor
        self.listing_manager.get_listing_by_id.return_value = listing
        self.comment_manager.create_comment.return_value = expected_result

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

        self.assertEqual(result, expected_result)
        self.assertEqual(result.id, 10)
        self.assertEqual(result.author_id, actor_id)
        self.assertEqual(result.listing_id, listing_id)

    # -----------------------------
    # create_comment - actor not found / lookup error
    # -----------------------------
    def test_create_comment_actor_lookup_error_raises_and_stops(self) -> None:
        actor_id = 999
        listing_id = 321
        comment = SimpleNamespace(
            id=None, listing_id=listing_id, author_id=actor_id, body="x"
        )

        self.account_manager.get_account_by_id.side_effect = Exception(
            "Actor not found"
        )

        with self.assertRaises(Exception) as ctx:
            self.service.create_comment(
                actor_id=actor_id, listing_id=listing_id, comment=comment
            )

        self.assertIn("Actor not found", str(ctx.exception))

        self.listing_manager.get_listing_by_id.assert_not_called()
        self.comment_manager.create_comment.assert_not_called()

    # -----------------------------
    # create_comment - listing not found / lookup error
    # -----------------------------
    def test_create_comment_listing_lookup_error_raises_and_stops(self) -> None:
        actor_id = 999
        listing_id = 321
        actor = SimpleNamespace(id=actor_id, verified=True)
        comment = SimpleNamespace(
            id=None, listing_id=listing_id, author_id=actor_id, body="x"
        )

        self.account_manager.get_account_by_id.return_value = actor
        self.listing_manager.get_listing_by_id.side_effect = Exception(
            "Listing not found"
        )

        with self.assertRaises(Exception) as ctx:
            self.service.create_comment(
                actor_id=actor_id, listing_id=listing_id, comment=comment
            )

        self.assertIn("Listing not found", str(ctx.exception))

        self.comment_manager.create_comment.assert_not_called()
