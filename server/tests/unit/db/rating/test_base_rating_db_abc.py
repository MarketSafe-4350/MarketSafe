from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from src.db import DBUtility
from src.db.rating import BaseRatingDB
from src.domain_models import Rating


class _BaseRatingDBCoverageShim(BaseRatingDB):
    def get_average_rating_by_account_id(self, account_id: int) -> float | None:
        return BaseRatingDB.get_average_rating_by_account_id(self, account_id)

    def get_sum_of_ratings_given_by_account_id(self, account_id: int) -> int:
        return BaseRatingDB.get_sum_of_ratings_given_by_account_id(self, account_id)

    def get_sum_of_ratings_received_by_account_id(self, account_id: int) -> int:
        return BaseRatingDB.get_sum_of_ratings_received_by_account_id(self, account_id)

    def get_by_listing_id(self, listing_id: int) -> Rating | None:
        return BaseRatingDB.get_by_listing_id(self, listing_id)

    def get_by_rater_id(self, rater_id: int):
        return BaseRatingDB.get_by_rater_id(self, rater_id)


class TestBaseRatingDBABC(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock(spec=DBUtility)
        self.sut = _BaseRatingDBCoverageShim(self.db)

    # -----------------------------
    # __init__
    # -----------------------------
    def test_init_stores_db(self) -> None:
        self.assertIs(self.sut._db, self.db)

    # -----------------------------
    # abstract methods raise
    # -----------------------------
    def test_get_average_rating_by_account_id_raises_not_implemented_error(
        self,
    ) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_average_rating_by_account_id(1)

    def test_get_sum_of_ratings_given_by_account_id_raises_not_implemented_error(
        self,
    ) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_sum_of_ratings_given_by_account_id(1)

    def test_get_sum_of_ratings_received_by_account_id_raises_not_implemented_error(
        self,
    ) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_sum_of_ratings_received_by_account_id(1)

    def test_get_by_listing_id_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_by_listing_id(10)

    def test_get_by_rater_id_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_by_rater_id(7)