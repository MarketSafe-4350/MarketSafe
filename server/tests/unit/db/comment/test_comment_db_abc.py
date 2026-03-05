from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from src.db import DBUtility
from src.domain_models import Comment
from src.db.comment import CommentDB


class _CommentDBCoverageShim(CommentDB):
    def add(self, comment: Comment) -> Comment:
        return CommentDB.add(self, comment)

    def get_by_id(self, comment_id: int):
        return CommentDB.get_by_id(self, comment_id)

    def get_by_listing_id(self, listing_id: int):
        return CommentDB.get_by_listing_id(self, listing_id)

    def get_by_author_id(self, author_id: int):
        return CommentDB.get_by_author_id(self, author_id)

    def update_body(self, comment_id: int, body: str | None) -> None:
        return CommentDB.update_body(self, comment_id, body)

    def remove(self, comment_id: int) -> bool:
        return CommentDB.remove(self, comment_id)


class TestCommentDBABC(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock(spec=DBUtility)
        self.sut = _CommentDBCoverageShim(self.db)

        self.sample_comment = Comment(
            comment_id=None,
            listing_id=1,
            author_id=2,
            body="hello",
            created_date=None,
        )

    # -----------------------------
    # __init__
    # -----------------------------
    def test_init_stores_db(self) -> None:
        self.assertIs(self.sut._db, self.db)

    # -----------------------------
    # abstract method bodies: raise NotImplementedError
    # -----------------------------
    def test_add_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.add(self.sample_comment)

    def test_get_by_id_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_by_id(1)

    def test_get_by_listing_id_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_by_listing_id(1)

    def test_get_by_author_id_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_by_author_id(2)

    def test_update_body_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.update_body(1, "new body")

    def test_update_body_accepts_none_and_still_raises_not_implemented_error(
        self,
    ) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.update_body(1, None)

    def test_remove_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.remove(1)
