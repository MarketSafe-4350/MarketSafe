from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from src.db import DBUtility
from src.domain_models import Listing
from src.db.listing import ListingDB


class _ListingDBCoverageShim(ListingDB):
    def add(self, listing: Listing) -> Listing:
        return ListingDB.add(self, listing)

    def get_by_id(self, listing_id: int):
        return ListingDB.get_by_id(self, listing_id)

    def get_all(self):
        return ListingDB.get_all(self)

    def get_by_seller_id(self, seller_id: int):
        return ListingDB.get_by_seller_id(self, seller_id)

    def get_by_buyer_id(self, buyer_id: int):
        return ListingDB.get_by_buyer_id(self, buyer_id)

    def get_unsold(self):
        return ListingDB.get_unsold(self)

    def get_recent_unsold(self, limit: int = 50, offset: int = 0):
        return ListingDB.get_recent_unsold(self, limit, offset)

    def get_unsold_by_location(self, location: str):
        return ListingDB.get_unsold_by_location(self, location)

    def get_unsold_by_max_price(self, max_price: float):
        return ListingDB.get_unsold_by_max_price(self, max_price)

    def get_unsold_by_location_and_max_price(self, location: str, max_price: float):
        return ListingDB.get_unsold_by_location_and_max_price(self, location, max_price)

    def find_unsold_by_title_keyword(
        self, keyword: str, limit: int = 50, offset: int = 0
    ):
        return ListingDB.find_unsold_by_title_keyword(self, keyword, limit, offset)

    def update(self, listing: Listing) -> Listing:
        return ListingDB.update(self, listing)

    def set_sold(self, listing_id: int, is_sold: bool, sold_to_id: int | None) -> None:
        return ListingDB.set_sold(self, listing_id, is_sold, sold_to_id)

    def set_price(self, listing_id: int, price: float) -> None:
        return ListingDB.set_price(self, listing_id, price)

    def remove(self, listing_id: int) -> bool:
        return ListingDB.remove(self, listing_id)


class TestListingDBABC(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock(spec=DBUtility)
        self.sut = _ListingDBCoverageShim(self.db)

        self.sample_listing = Listing(
            listing_id=None,
            seller_id=1,
            title="Test",
            description="Desc",
            price=10.0,
            location="Winnipeg",
            image_url=None,
            is_sold=False,
            sold_to_id=None,
            created_at=None,
        )

    # -----------------------------
    # __init__
    # -----------------------------
    def test_init_stores_db(self) -> None:
        self.assertIs(self.sut._db, self.db)

    def test_add_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.add(self.sample_listing)

    def test_get_by_id_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_by_id(1)

    def test_get_all_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_all()

    def test_get_by_seller_id_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_by_seller_id(1)

    def test_get_by_buyer_id_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_by_buyer_id(2)

    def test_get_unsold_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_unsold()

    def test_get_recent_unsold_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_recent_unsold()

    def test_get_recent_unsold_with_args_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_recent_unsold(limit=10, offset=5)

    def test_get_unsold_by_location_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_unsold_by_location("Winnipeg")

    def test_get_unsold_by_max_price_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_unsold_by_max_price(50.0)

    def test_get_unsold_by_location_and_max_price_raises_not_implemented_error(
        self,
    ) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_unsold_by_location_and_max_price("Winnipeg", 50.0)

    def test_find_unsold_by_title_keyword_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.find_unsold_by_title_keyword("bike")

    def test_find_unsold_by_title_keyword_with_args_raises_not_implemented_error(
        self,
    ) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.find_unsold_by_title_keyword("bike", limit=5, offset=10)

    def test_update_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.update(self.sample_listing)

    def test_set_sold_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.set_sold(1, True, 2)

    def test_set_sold_allows_none_sold_to_id_and_raises_not_implemented_error(
        self,
    ) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.set_sold(1, False, None)

    def test_set_price_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.set_price(1, 99.99)

    def test_remove_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.remove(1)
