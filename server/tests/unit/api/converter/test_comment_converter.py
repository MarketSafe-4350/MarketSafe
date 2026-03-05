from __future__ import annotations

import unittest
from datetime import datetime, timezone

from src.api.converter.comment_converter import (
    CommentCreate,
    CommentResponse,
)
from src.domain_models.comment import Comment
from src.domain_models.account import Account


class TestCommentConverter(unittest.TestCase):
    # -----------------------------
    # CommentCreate.to_domain
    # -----------------------------
    def test_comment_create_to_domain_sets_fields(self) -> None:
        dto = CommentCreate(body="hello")

        out = dto.to_domain(listing_id=10, author_id=7)

        self.assertIsInstance(out, Comment)
        self.assertEqual(out.listing_id, 10)
        self.assertEqual(out.author_id, 7)
        self.assertEqual(out.body, "hello")

    def test_comment_create_to_domain_allows_none_body(self) -> None:
        dto = CommentCreate(body=None)

        out = dto.to_domain(listing_id=1, author_id=2)

        self.assertIsNone(out.body)
        self.assertEqual(out.listing_id, 1)
        self.assertEqual(out.author_id, 2)

    # -----------------------------
    # CommentResponse.from_domain
    # -----------------------------
    def test_comment_response_from_domain_maps_all_fields_with_created_date(
        self,
    ) -> None:
        created = datetime(2026, 3, 4, 12, 30, 0, tzinfo=timezone.utc)

        comment = Comment(
            comment_id=5,
            listing_id=10,
            author_id=7,
            body="hi",
            created_date=created,
        )

        author = Account(
            account_id=7,
            email="a@b.com",
            password="hashed",
            fname="Test",
            lname="User",
            verified=True,
        )

        out = CommentResponse.from_domain(comment, author)

        self.assertEqual(out.id, 5)
        self.assertEqual(out.listing_id, 10)
        self.assertEqual(out.author_id, 7)
        self.assertEqual(out.author_name, "Test User")
        self.assertEqual(out.body, "hi")
        self.assertEqual(out.created_date, created.isoformat())

    def test_comment_response_from_domain_handles_none_created_date(self) -> None:
        comment = Comment(
            comment_id=1,
            listing_id=2,
            author_id=3,
            body=None,
            created_date=None,
        )

        author = Account(
            account_id=3,
            email="x@y.com",
            password="hashed",
            fname="A",
            lname="B",
            verified=False,
        )

        out = CommentResponse.from_domain(comment, author)

        self.assertEqual(out.id, 1)
        self.assertEqual(out.author_name, "A B")
        self.assertIsNone(out.body)
        self.assertIsNone(out.created_date)
