from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.db import DBUtility
from src.db.comment.mysql import MySQLCommentDB
from src.domain_models import Comment
from src.utils import DatabaseQueryError, CommentNotFoundError


class TestMySQLCommentDB(unittest.TestCase):
    def setUp(self) -> None:
        self.db_util: MagicMock = MagicMock(spec=DBUtility)
        self.comment_db = MySQLCommentDB(self.db_util)

        self.conn: MagicMock = MagicMock()

        self.connect_cm: MagicMock = MagicMock()
        self.connect_cm.__enter__.return_value = self.conn
        self.connect_cm.__exit__.return_value = False

        self.tx_cm: MagicMock = MagicMock()
        self.tx_cm.__enter__.return_value = self.conn
        self.tx_cm.__exit__.return_value = False

        self.db_util.connect.return_value = self.connect_cm
        self.db_util.transaction.return_value = self.tx_cm

    def _comment(
        self,
        *,
        comment_id: int | None = None,
        listing_id: int = 10,
        author_id: int = 20,
        body: str | None = "hello",
    ) -> Comment:
        return Comment(
            listing_id=listing_id,
            author_id=author_id,
            body=body,
            comment_id=comment_id,
        )

    # -----------------------------
    # add
    # -----------------------------
    def test_add_inserts_and_returns_comment_with_new_id(self) -> None:
        c = self._comment(comment_id=None, listing_id=10, author_id=20, body="hi")

        exec_result = MagicMock()
        exec_result.lastrowid = 123
        self.conn.execute.return_value = exec_result

        out = self.comment_db.add(c)

        self.assertEqual(out.id, 123)
        self.assertEqual(out.listing_id, 10)
        self.assertEqual(out.author_id, 20)
        self.assertEqual(out.body, "hi")

        self.db_util.transaction.assert_called_once()
        self.conn.execute.assert_called_once()

    def test_add_raises_database_query_error_on_integrity_error(self) -> None:
        c = self._comment()
        self.conn.execute.side_effect = IntegrityError("stmt", {}, Exception("fk fail"))

        with self.assertRaises(DatabaseQueryError):
            self.comment_db.add(c)

    def test_add_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        c = self._comment()
        self.conn.execute.side_effect = SQLAlchemyError("db fail")

        with self.assertRaises(DatabaseQueryError):
            self.comment_db.add(c)

    # -----------------------------
    # get_by_id
    # -----------------------------
    def test_get_by_id_returns_none_when_missing(self) -> None:
        exec_result = MagicMock()
        exec_result.mappings.return_value.first.return_value = None
        self.conn.execute.return_value = exec_result

        out = self.comment_db.get_by_id(999)
        self.assertIsNone(out)

        self.db_util.connect.assert_called_once()
        self.conn.execute.assert_called_once()

    def test_get_by_id_returns_comment_when_found(self) -> None:
        row = {
            "id": 5,
            "created_date": None,
            "body": "hello",
            "listing_id": 10,
            "author_id": 20,
        }

        exec_result = MagicMock()
        exec_result.mappings.return_value.first.return_value = row
        self.conn.execute.return_value = exec_result

        expected = self._comment(
            comment_id=5, listing_id=10, author_id=20, body="hello"
        )

        with patch(
            f"{MySQLCommentDB.__module__}.CommentMapper.from_mapping",
            return_value=expected,
        ) as mapper:
            out = self.comment_db.get_by_id(5)

        self.assertIs(out, expected)
        mapper.assert_called_once()

    def test_get_by_id_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.comment_db.get_by_id(1)

    # -----------------------------
    # get_by_listing_id
    # -----------------------------
    def test_get_by_listing_id_returns_empty_list_when_none(self) -> None:
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = []
        self.conn.execute.return_value = exec_result

        out = self.comment_db.get_by_listing_id(10)
        self.assertEqual(out, [])

    def test_get_by_listing_id_maps_rows(self) -> None:
        rows = [
            {
                "id": 1,
                "created_date": None,
                "body": "a",
                "listing_id": 10,
                "author_id": 20,
            },
            {
                "id": 2,
                "created_date": None,
                "body": "b",
                "listing_id": 10,
                "author_id": 21,
            },
        ]

        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = rows
        self.conn.execute.return_value = exec_result

        c1 = self._comment(comment_id=1, listing_id=10, author_id=20, body="a")
        c2 = self._comment(comment_id=2, listing_id=10, author_id=21, body="b")

        with patch(f"{MySQLCommentDB.__module__}.CommentMapper.from_mapping") as mapper:
            mapper.side_effect = [c1, c2]
            out = self.comment_db.get_by_listing_id(10)

        self.assertEqual(out, [c1, c2])
        self.assertEqual(mapper.call_count, 2)

    def test_get_by_listing_id_raises_database_query_error_on_sqlalchemy_error(
        self,
    ) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.comment_db.get_by_listing_id(10)

    # -----------------------------
    # get_by_author_id
    # -----------------------------
    def test_get_by_author_id_returns_empty_list_when_none(self) -> None:
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = []
        self.conn.execute.return_value = exec_result

        out = self.comment_db.get_by_author_id(20)
        self.assertEqual(out, [])

    def test_get_by_author_id_maps_rows(self) -> None:
        rows = [
            {
                "id": 1,
                "created_date": None,
                "body": "a",
                "listing_id": 10,
                "author_id": 20,
            },
            {
                "id": 2,
                "created_date": None,
                "body": "b",
                "listing_id": 11,
                "author_id": 20,
            },
        ]

        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = rows
        self.conn.execute.return_value = exec_result

        c1 = self._comment(comment_id=1, listing_id=10, author_id=20, body="a")
        c2 = self._comment(comment_id=2, listing_id=11, author_id=20, body="b")

        with patch(f"{MySQLCommentDB.__module__}.CommentMapper.from_mapping") as mapper:
            mapper.side_effect = [c1, c2]
            out = self.comment_db.get_by_author_id(20)

        self.assertEqual(out, [c1, c2])
        self.assertEqual(mapper.call_count, 2)

    def test_get_by_author_id_raises_database_query_error_on_sqlalchemy_error(
        self,
    ) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.comment_db.get_by_author_id(20)

    # -----------------------------
    # update_body
    # -----------------------------
    def test_update_body_updates_when_row_exists(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 1
        self.conn.execute.return_value = exec_result

        self.comment_db.update_body(10, "new body")

        self.db_util.transaction.assert_called_once()
        self.conn.execute.assert_called_once()

    def test_update_body_raises_comment_not_found_when_rowcount_zero(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 0
        self.conn.execute.return_value = exec_result

        with self.assertRaises(CommentNotFoundError):
            self.comment_db.update_body(999, "x")

    def test_update_body_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.comment_db.update_body(1, "x")

    def test_update_body_allows_none_body(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 1
        self.conn.execute.return_value = exec_result

        self.comment_db.update_body(10, None)

        _, kwargs = self.conn.execute.call_args
        params = self.conn.execute.call_args[0][1]
        self.assertEqual(params["id"], 10)
        self.assertIsNone(params["body"])

    def test_update_body_validates_body_when_not_none(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 1
        self.conn.execute.return_value = exec_result

        with patch(
            f"{MySQLCommentDB.__module__}.Validation.require_str",
            return_value="trimmed",
        ) as req_str:
            self.comment_db.update_body(10, "  hello  ")

        req_str.assert_called_once_with("  hello  ", "body")

        params = self.conn.execute.call_args[0][1]
        self.assertEqual(params["id"], 10)
        self.assertEqual(params["body"], "trimmed")

    # -----------------------------
    # remove
    # -----------------------------
    def test_remove_returns_true_when_deleted(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 1
        self.conn.execute.return_value = exec_result

        out = self.comment_db.remove(5)
        self.assertTrue(out)

    def test_remove_returns_false_when_missing(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 0
        self.conn.execute.return_value = exec_result

        out = self.comment_db.remove(999)
        self.assertFalse(out)

    def test_remove_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.comment_db.remove(1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
