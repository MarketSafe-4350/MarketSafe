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

    @staticmethod
    def _sample_row(
        rating_id: int = 10,
        transaction_rating: int = 5,
        listing_id: int = 20,
        rater_id: int = 30,
        created_at: str = "2026-03-12 10:00:00",
    ) -> dict:
        return {
            "id": rating_id,
            "created_at": created_at,
            "transaction_rating": transaction_rating,
            "listing_id": listing_id,
            "rater_id": rater_id,
        }

    # -----------------------------
    # AGGREGATES
    # -----------------------------
    def test_get_average_rating_by_account_id_returns_float(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(first={"avg_rating": 4.5})
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.get_average_rating_by_account_id(1)

        self.assertEqual(4.5, out)

    def test_get_sum_of_ratings_given_by_account_id_returns_sum(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(first={"total_rating_sum": 17})
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.get_sum_of_ratings_given_by_account_id(1)

        self.assertEqual(17, out)

    def test_get_sum_of_ratings_given_by_account_id_returns_zero_when_none(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(first={"total_rating_sum": None})
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.get_sum_of_ratings_given_by_account_id(1)

        self.assertEqual(0, out)

    def test_get_sum_of_ratings_received_by_account_id_returns_sum(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(first={"total_rating_sum": 12})
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.get_sum_of_ratings_received_by_account_id(1)

        self.assertEqual(12, out)

    def test_get_sum_of_ratings_received_by_account_id_returns_zero_when_none(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(first={"total_rating_sum": None})
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.get_sum_of_ratings_received_by_account_id(1)

        self.assertEqual(0, out)

    def test_get_average_for_rater_returns_float(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(first={"avg_rating": 3.75})
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.get_average_for_rater(1)

        self.assertEqual(3.75, out)

    def test_get_average_for_rater_returns_none_when_row_none(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(first=None)
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.get_average_for_rater(1)

        self.assertIsNone(out)

    def test_get_average_for_rater_returns_none_when_avg_none(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(first={"avg_rating": None})
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.get_average_for_rater(1)

        self.assertIsNone(out)

    def test_count_by_rater_returns_count(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(first={"rating_count": 4})
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.count_by_rater(1)

        self.assertEqual(4, out)

    def test_count_by_rater_returns_zero_when_none(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(first={"rating_count": None})
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.count_by_rater(1)

        self.assertEqual(0, out)

    # -----------------------------
    # CREATE
    # -----------------------------
    def test_add_returns_new_rating(self) -> None:
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=5)

        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(lastrowid=99)
        self.db.transaction.return_value = self._mock_connect_ctx(conn)

        out = self.repo.add(rating)

        self.assertIsInstance(out, Rating)
        self.assertEqual(99, out.id)
        self.assertEqual(1, out.listing_id)
        self.assertEqual(2, out.rater_id)
        self.assertEqual(5, out.transaction_rating)

    def test_add_raises_database_query_error_on_integrity_error(self) -> None:
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=5)

        conn = MagicMock()
        conn.execute.side_effect = IntegrityError("stmt", {"listing_id": 1}, Exception("orig"))
        self.db.transaction.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(DatabaseQueryError):
            self.repo.add(rating)

    # -----------------------------
    # READ
    # -----------------------------
    @patch("src.db.rating.mysql.mysql_rating_db.RatingMapper.from_mapping")
    def test_get_by_id_returns_rating(self, mock_from_mapping: MagicMock) -> None:
        mapped = Rating(listing_id=20, rater_id=30, transaction_rating=5, rating_id=10)
        mock_from_mapping.return_value = mapped

        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(first=self._sample_row())
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.get_by_id(10)

        self.assertIs(mapped, out)
        mock_from_mapping.assert_called_once()

    def test_get_by_id_returns_none_when_missing(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(first=None)
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.get_by_id(10)

        self.assertIsNone(out)

    @patch("src.db.rating.mysql.mysql_rating_db.RatingMapper.from_mapping")
    def test_get_by_listing_id_returns_rating(self, mock_from_mapping: MagicMock) -> None:
        mapped = Rating(listing_id=20, rater_id=30, transaction_rating=5, rating_id=10)
        mock_from_mapping.return_value = mapped

        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(first=self._sample_row())
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.get_by_listing_id(20)

        self.assertIs(mapped, out)
        mock_from_mapping.assert_called_once()

    def test_get_by_listing_id_returns_none_when_missing(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(first=None)
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.get_by_listing_id(20)

        self.assertIsNone(out)

    @patch("src.db.rating.mysql.mysql_rating_db.RatingMapper.from_mapping")
    def test_get_by_rater_id_returns_list(self, mock_from_mapping: MagicMock) -> None:
        rows = [self._sample_row(rating_id=1), self._sample_row(rating_id=2)]
        mapped = [
            Rating(listing_id=20, rater_id=30, transaction_rating=5, rating_id=1),
            Rating(listing_id=20, rater_id=30, transaction_rating=5, rating_id=2),
        ]
        mock_from_mapping.side_effect = mapped

        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(all_rows=rows)
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.get_by_rater_id(30)

        self.assertEqual(mapped, out)
        self.assertEqual(2, mock_from_mapping.call_count)

    def test_get_by_rater_id_returns_empty_list(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(all_rows=[])
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.get_by_rater_id(30)

        self.assertEqual([], out)

    @patch("src.db.rating.mysql.mysql_rating_db.RatingMapper.from_mapping")
    def test_get_all_returns_list(self, mock_from_mapping: MagicMock) -> None:
        rows = [self._sample_row(rating_id=1), self._sample_row(rating_id=2)]
        mapped = [
            Rating(listing_id=20, rater_id=30, transaction_rating=5, rating_id=1),
            Rating(listing_id=20, rater_id=30, transaction_rating=5, rating_id=2),
        ]
        mock_from_mapping.side_effect = mapped

        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(all_rows=rows)
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.get_all()

        self.assertEqual(mapped, out)
        self.assertEqual(2, mock_from_mapping.call_count)

    @patch("src.db.rating.mysql.mysql_rating_db.RatingMapper.from_mapping")
    def test_get_recent_returns_list(self, mock_from_mapping: MagicMock) -> None:
        rows = [self._sample_row(rating_id=1), self._sample_row(rating_id=2)]
        mapped = [
            Rating(listing_id=20, rater_id=30, transaction_rating=5, rating_id=1),
            Rating(listing_id=20, rater_id=30, transaction_rating=5, rating_id=2),
        ]
        mock_from_mapping.side_effect = mapped

        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(all_rows=rows)
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.get_recent(limit=2, offset=0)

        self.assertEqual(mapped, out)

    @patch("src.db.rating.mysql.mysql_rating_db.RatingMapper.from_mapping")
    def test_get_by_score_returns_list(self, mock_from_mapping: MagicMock) -> None:
        rows = [self._sample_row(rating_id=1, transaction_rating=5)]
        mapped = [Rating(listing_id=20, rater_id=30, transaction_rating=5, rating_id=1)]
        mock_from_mapping.side_effect = mapped

        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(all_rows=rows)
        self.db.connect.return_value = self._mock_connect_ctx(conn)

        out = self.repo.get_by_score(5)

        self.assertEqual(mapped, out)

    # -----------------------------
    # UPDATE
    # -----------------------------
    def test_update_raises_rating_not_found_when_rowcount_zero(self) -> None:
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=5, rating_id=10)

        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(rowcount=0)
        self.db.transaction.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(RatingNotFoundError):
            self.repo.update(rating)

    def test_update_returns_updated_rating(self) -> None:
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=5, rating_id=10)
        updated = Rating(listing_id=11, rater_id=22, transaction_rating=4, rating_id=10)

        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(rowcount=1)
        self.db.transaction.return_value = self._mock_connect_ctx(conn)

        with patch.object(self.repo, "get_by_id", return_value=updated) as mock_get_by_id:
            out = self.repo.update(rating)

        self.assertIs(updated, out)
        mock_get_by_id.assert_called_once_with(10)

    def test_update_raises_when_rating_is_none(self) -> None:
        with self.assertRaises(ValidationError):
            self.repo.update(None)  # type: ignore[arg-type]

    def test_update_raises_when_rating_id_is_none(self) -> None:
        rating = Rating(listing_id=1, rater_id=2, transaction_rating=5)

        with self.assertRaises(ValidationError):
            self.repo.update(rating)

    def test_set_score_raises_rating_not_found_when_rowcount_zero(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(rowcount=0)
        self.db.transaction.return_value = self._mock_connect_ctx(conn)

        with self.assertRaises(RatingNotFoundError):
            self.repo.set_score(1, 5)

    def test_set_score_succeeds_when_rowcount_positive(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(rowcount=1)
        self.db.transaction.return_value = self._mock_connect_ctx(conn)

        out = self.repo.set_score(1, 5)

        self.assertIsNone(out)

    # -----------------------------
    # DELETE
    # -----------------------------
    def test_remove_returns_true_when_deleted(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(rowcount=1)
        self.db.transaction.return_value = self._mock_connect_ctx(conn)

        out = self.repo.remove(1)

        self.assertTrue(out)

    def test_remove_returns_false_when_nothing_deleted(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(rowcount=0)
        self.db.transaction.return_value = self._mock_connect_ctx(conn)

        out = self.repo.remove(1)

        self.assertFalse(out)

    def test_remove_by_listing_id_returns_true_when_deleted(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(rowcount=2)
        self.db.transaction.return_value = self._mock_connect_ctx(conn)

        out = self.repo.remove_by_listing_id(1)

        self.assertTrue(out)

    def test_remove_by_listing_id_returns_false_when_nothing_deleted(self) -> None:
        conn = MagicMock()
        conn.execute.return_value = self._make_mapping_result(rowcount=0)
        self.db.transaction.return_value = self._mock_connect_ctx(conn)

        out = self.repo.remove_by_listing_id(1)

        self.assertFalse(out)