from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from src.db.rating.mysql.mysql_rating_db import MySQLRatingDB
from src.domain_models import Rating
from src.utils import (
    ValidationError,
    DatabaseQueryError,
    RatingNotFoundError,
)


class TestMySQLRatingDBUnit(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock()
        self.repo = MySQLRatingDB(self.db)

    @staticmethod
    def _mock_connect_ctx(conn: MagicMock) -> MagicMock:
        ctx = MagicMock()
        ctx.__enter__.return_value = conn
        ctx.__exit__.return_value = False
        return ctx

    @staticmethod
    def _make_mapping_result(*, first=None, all_rows=None, rowcount=None, lastrowid=None) -> MagicMock:
        result = MagicMock()
        mappings = MagicMock()
        mappings.first.return_value = first
        mappings.all.return_value = all_rows if all_rows is not None else []
        result.mappings.return_value = mappings
        result.rowcount = rowcount
        result.lastrowid = lastrowid
        return result

    def test_get_average_rating_by_account_id_returns_none_when_avg_is_none(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(first={"avg_rating": None})
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.get_average_rating_by_account_id(1)

        self.assertIsNone(out)

    def test_get_sum_of_ratings_given_by_account_id_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_sum_of_ratings_given_by_account_id(1)

    def test_get_sum_of_ratings_received_by_account_id_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_sum_of_ratings_received_by_account_id(1)

    def test_add_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=5)

        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.transaction.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.add(rating)

    def test_get_by_id_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_by_id(1)

    def test_get_by_listing_id_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_by_listing_id(1)

    def test_get_by_rater_id_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_by_rater_id(1)

    def test_get_all_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_all()

    def test_get_recent_raises_when_limit_negative(self) -> None:
        with self.assertRaises(ValidationError):
            self.repo.get_recent(limit=-1, offset=0)

    def test_get_recent_raises_when_offset_negative(self) -> None:
        with self.assertRaises(ValidationError):
            self.repo.get_recent(limit=10, offset=-1)

    def test_get_recent_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_recent(limit=10, offset=0)

    def test_get_by_score_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_by_score(5)

    def test_get_average_for_rater_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_average_for_rater(1)

    def test_count_by_rater_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.count_by_rater(1)

    def test_update_raises_rating_not_found_when_get_by_id_returns_none_after_update(self) -> None:
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=5, rating_id=10)

        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(rowcount=1)
        self.db.transaction.return_value = self._mock_connect_ctx(conn)

        with patch.object(self.repo, "get_by_id", return_value=None):
            with self.assertRaises(RatingNotFoundError):
                self.repo.update(rating)

    def test_update_raises_database_query_error_on_integrity_error(self) -> None:
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=5, rating_id=10)

        conn = MagicMock()
        conn.execute.side_effect = IntegrityError("stmt", {"id": 10}, Exception("orig"))
        self.db.transaction.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.update(rating)

    def test_update_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=5, rating_id=10)

        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.transaction.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.update(rating)

    def test_set_score_raises_database_query_error_on_integrity_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = IntegrityError("stmt", {"id": 1}, Exception("orig"))
        self.db.transaction.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.set_score(1, 5)

    def test_set_score_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.transaction.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.set_score(1, 5)

    def test_remove_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.transaction.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.remove(1)

    def test_remove_by_listing_id_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.transaction.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.remove_by_listing_id(1)

    def test_get_average_rating_by_account_id_returns_none_when_row_is_none(self) -> None:
        conn = MagicMock()
        result = MagicMock()
        mappings = MagicMock()
        mappings.first.return_value = None
        result.mappings.return_value = mappings
        conn.execute.return_value = result

        ctx = MagicMock()
        ctx.__enter__.return_value = conn
        ctx.__exit__.return_value = False
        self.db.connect.return_value = ctx

        out = self.repo.get_average_rating_by_account_id(1)

        self.assertIsNone(out)
        conn.execute.assert_called_once()

    def test_get_average_rating_by_account_id_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_average_rating_by_account_id(1)
