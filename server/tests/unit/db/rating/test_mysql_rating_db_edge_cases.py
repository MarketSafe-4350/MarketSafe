

import unittest
from unittest.mock import MagicMock

from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from src.db.rating.mysql.mysql_rating_db import MySQLRatingDB
from src.domain_models import Rating
from src.utils import ValidationError, DatabaseQueryError, RatingNotFoundError

class TestMySQLRatingDBEdgeCases(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock()
        self.repo = MySQLRatingDB(self.db)

    @staticmethod
    def _mock_ctx(conn: MagicMock) -> MagicMock:
        ctx = MagicMock()
        ctx.__enter__.return_value = conn
        ctx.__exit__.return_value = False
        return ctx

    @staticmethod
    def _mapping_result(*, first=None, all_rows=None, rowcount=None, lastrowid=None) -> MagicMock:
        result = MagicMock()
        mappings = MagicMock()
        mappings.first.return_value = first
        mappings.all.return_value = [] if all_rows is None else all_rows
        result.mappings.return_value = mappings
        result.rowcount = rowcount
        result.lastrowid = lastrowid
        return result

    # -----------------------------
    # get_average_rating_by_account_id
    # lines 55, 57-58
    # -----------------------------
    def test_get_average_rating_by_account_id_returns_none_when_row_missing(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._mapping_result(first=None)
        self.db.connect.return_value = self._mock_ctx(conn)

        out = self.repo.get_average_rating_by_account_id(1)

        self.assertIsNone(out)

    def test_get_average_rating_by_account_id_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_average_rating_by_account_id(1)

    # -----------------------------
    # sum queries
    # lines 80-81, 106-107
    # -----------------------------
    def test_get_sum_of_ratings_given_by_account_id_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_sum_of_ratings_given_by_account_id(1)

    def test_get_sum_of_ratings_received_by_account_id_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_sum_of_ratings_received_by_account_id(1)

    # -----------------------------
    # read methods
    # lines 153-154, 176-177, 196-197, 217-218, 235-236
    # -----------------------------
    def test_get_by_id_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_by_id(1)

    def test_get_by_listing_id_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_by_listing_id(1)

    def test_get_by_rater_id_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_by_rater_id(1)

    def test_get_all_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_all()

    def test_get_recent_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_recent(limit=10, offset=0)

    # -----------------------------
    # get_recent validation
    # lines 247, 249
    # -----------------------------
    def test_get_recent_raises_validation_error_when_limit_negative(self) -> None:
        with self.assertRaises(ValidationError):
            self.repo.get_recent(limit=-1, offset=0)

    def test_get_recent_raises_validation_error_when_offset_negative(self) -> None:
        with self.assertRaises(ValidationError):
            self.repo.get_recent(limit=10, offset=-1)

    # -----------------------------
    # remaining aggregate queries
    # lines 265-266, 288-289, 313-314, 333-334
    # -----------------------------
    def test_get_by_score_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_by_score(5)

    def test_get_average_for_rater_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.get_average_for_rater(1)

    def test_count_by_rater_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.connect.return_value = self._mock_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.count_by_rater(1)

    def test_add_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=5)

        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.transaction.return_value = self._mock_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.add(rating)

    # -----------------------------
    # update
    # lines 372, 380-386
    # -----------------------------
    def test_update_raises_rating_not_found_when_get_by_id_returns_none_after_successful_update(self) -> None:
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=5, rating_id=10)

        conn = MagicMock()
        conn.execute.return_value = self._mapping_result(rowcount=1)
        self.db.transaction.return_value = self._mock_ctx(conn)

        original_get_by_id = self.repo.get_by_id
        self.repo.get_by_id = MagicMock(return_value=None)
        try:
            with self.assertRaises(RatingNotFoundError):
                self.repo.update(rating)
        finally:
            self.repo.get_by_id = original_get_by_id

    def test_update_raises_database_query_error_on_integrity_error(self) -> None:
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=5, rating_id=10)

        conn = MagicMock()
        conn.execute.side_effect = IntegrityError("stmt", {"id": 10}, Exception("orig"))
        self.db.transaction.return_value = self._mock_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.update(rating)

    def test_update_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=5, rating_id=10)

        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.transaction.return_value = self._mock_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.update(rating)

    # -----------------------------
    # set_score
    # lines 417-423
    # -----------------------------
    def test_set_score_raises_rating_not_found_when_rowcount_zero(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._mapping_result(rowcount=0)
        self.db.transaction.return_value = self._mock_ctx(conn)

        with self.assertRaises(RatingNotFoundError):
            self.repo.set_score(1, 5)

    def test_set_score_raises_database_query_error_on_integrity_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = IntegrityError("stmt", {"id": 1}, Exception("orig"))
        self.db.transaction.return_value = self._mock_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.set_score(1, 5)

    def test_set_score_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.transaction.return_value = self._mock_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.set_score(1, 5)

    # -----------------------------
    # delete
    # lines 445-446, 465-466
    # -----------------------------
    def test_remove_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.transaction.return_value = self._mock_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.remove(1)

    def test_remove_by_listing_id_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError("boom")
        self.db.transaction.return_value = self._mock_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.remove_by_listing_id(1)