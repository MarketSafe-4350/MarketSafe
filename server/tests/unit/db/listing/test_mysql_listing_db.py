from __future__ import annotations

import unittest
from datetime import datetime
from unittest.mock import MagicMock

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.db import DBUtility
from src.domain_models import Listing
from src.utils import DatabaseQueryError, ListingNotFoundError
from src.db.listing.mysql.mysql_listing_db import MySQLListingDB


class TestMySQLListingDB(unittest.TestCase):
    def setUp(self) -> None:
        self.db_util: MagicMock = MagicMock(spec=DBUtility)
        self.sut = MySQLListingDB(self.db_util)

        self.conn: MagicMock = MagicMock()

        self.connect_cm: MagicMock = MagicMock()
        self.connect_cm.__enter__.return_value = self.conn
        self.connect_cm.__exit__.return_value = False

        self.tx_cm: MagicMock = MagicMock()
        self.tx_cm.__enter__.return_value = self.conn
        self.tx_cm.__exit__.return_value = False

        self.db_util.connect.return_value = self.connect_cm
        self.db_util.transaction.return_value = self.tx_cm

    def _listing(
        self,
        *,
        listing_id: int | None = None,
        seller_id: int = 1,
        title: str = " Title ",
        description: str = " Desc ",
        price: float = 10.0,
        image_url: str | None = " http://img ",
        location: str | None = " Winnipeg ",
        is_sold: bool = False,
        sold_to_id: int | None = None,
        created_at: datetime | None = None,
    ) -> Listing:
        """
        Adjust the constructor args to match your Listing model exactly.
        """
        return Listing(
            listing_id=listing_id,
            seller_id=seller_id,
            title=title,
            description=description,
            price=price,
            image_url=image_url,
            location=location,
            is_sold=is_sold,
            sold_to_id=sold_to_id,
            created_at=created_at,
        )

    # -----------------------------
    # add
    # -----------------------------
    def test_add_inserts_and_returns_listing_with_new_id(self) -> None:
        listing = self._listing(
            listing_id=None, title="Bike", description="Nice", price=50.0
        )

        exec_result = MagicMock()
        exec_result.lastrowid = 123
        self.conn.execute.return_value = exec_result

        out = self.sut.add(listing)

        self.db_util.transaction.assert_called_once()
        self.conn.execute.assert_called_once()

        self.assertEqual(out.id, 123)
        self.assertEqual(out.seller_id, 1)
        self.assertEqual(out.title, "Bike")
        self.assertEqual(out.description, "Nice")
        self.assertEqual(out.price, 50.0)
        # image/location are stripped
        self.assertEqual(out.image_url, "http://img")
        self.assertEqual(out.location, "Winnipeg")
        self.assertFalse(bool(out.is_sold))
        self.assertIsNone(out.sold_to_id)

    def test_add_raises_database_query_error_on_integrity_error(self) -> None:
        listing = self._listing(title="X", description="Y", price=1.0)
        self.conn.execute.side_effect = IntegrityError(
            "stmt", {}, Exception("fk/constraint")
        )

        with self.assertRaises(DatabaseQueryError):
            self.sut.add(listing)

    def test_add_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        listing = self._listing(title="X", description="Y", price=1.0)
        self.conn.execute.side_effect = SQLAlchemyError("boom")

        with self.assertRaises(DatabaseQueryError):
            self.sut.add(listing)

    # -----------------------------
    # get_by_id
    # -----------------------------
    def test_get_by_id_returns_none_when_missing(self) -> None:
        exec_result = MagicMock()
        exec_result.mappings.return_value.first.return_value = None
        self.conn.execute.return_value = exec_result

        out = self.sut.get_by_id(999)
        self.assertIsNone(out)

        self.db_util.connect.assert_called_once()
        self.conn.execute.assert_called_once()

    def test_get_by_id_returns_listing_when_found(self) -> None:
        now = datetime.utcnow()
        row = {
            "id": 5,
            "seller_id": 1,
            "title": "Bike",
            "description": "Nice",
            "image_url": None,
            "price": 50.0,
            "location": "Winnipeg",
            "created_at": now,
            "is_sold": 0,
            "sold_to_id": None,
        }

        exec_result = MagicMock()
        exec_result.mappings.return_value.first.return_value = row
        self.conn.execute.return_value = exec_result

        out = self.sut.get_by_id(5)
        self.assertIsNotNone(out)
        self.assertEqual(out.id, 5)
        self.assertEqual(out.title, "Bike")
        self.assertEqual(out.created_at, now)

    def test_get_by_id_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.get_by_id(1)

    # -----------------------------
    # get_all
    # -----------------------------
    def test_get_all_returns_list(self) -> None:
        now = datetime.utcnow()
        rows = [
            {
                "id": 1,
                "seller_id": 1,
                "title": "A",
                "description": "DA",
                "image_url": None,
                "price": 1.0,
                "location": None,
                "created_at": now,
                "is_sold": 0,
                "sold_to_id": None,
            },
            {
                "id": 2,
                "seller_id": 2,
                "title": "B",
                "description": "DB",
                "image_url": "x",
                "price": 2.0,
                "location": "Winnipeg",
                "created_at": now,
                "is_sold": 1,
                "sold_to_id": 9,
            },
        ]

        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = rows
        self.conn.execute.return_value = exec_result

        out = self.sut.get_all()
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0].id, 1)
        self.assertEqual(out[1].id, 2)

    def test_get_all_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.get_all()

    # -----------------------------
    # get_by_seller_id
    # -----------------------------
    def test_get_by_seller_id_returns_list(self) -> None:
        now = datetime.utcnow()
        rows = [
            {
                "id": 10,
                "seller_id": 7,
                "title": "X",
                "description": "DX",
                "image_url": None,
                "price": 3.0,
                "location": None,
                "created_at": now,
                "is_sold": 0,
                "sold_to_id": None,
            }
        ]

        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = rows
        self.conn.execute.return_value = exec_result

        out = self.sut.get_by_seller_id(7)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].seller_id, 7)

    def test_get_by_seller_id_raises_database_query_error_on_sqlalchemy_error(
        self,
    ) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.get_by_seller_id(1)

    # -----------------------------
    # get_by_buyer_id
    # -----------------------------
    def test_get_by_buyer_id_returns_list(self) -> None:
        now = datetime.utcnow()
        rows = [
            {
                "id": 20,
                "seller_id": 1,
                "title": "Sold",
                "description": "DS",
                "image_url": None,
                "price": 5.0,
                "location": None,
                "created_at": now,
                "is_sold": 1,
                "sold_to_id": 99,
            }
        ]

        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = rows
        self.conn.execute.return_value = exec_result

        out = self.sut.get_by_buyer_id(99)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].sold_to_id, 99)

    def test_get_by_buyer_id_raises_database_query_error_on_sqlalchemy_error(
        self,
    ) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.get_by_buyer_id(1)

    # -----------------------------
    # get_unsold
    # -----------------------------
    def test_get_unsold_returns_list(self) -> None:
        now = datetime.utcnow()
        rows = [
            {
                "id": 1,
                "seller_id": 1,
                "title": "Unsold",
                "description": "D",
                "image_url": None,
                "price": 1.0,
                "location": "W",
                "created_at": now,
                "is_sold": 0,
                "sold_to_id": None,
            }
        ]
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = rows
        self.conn.execute.return_value = exec_result

        out = self.sut.get_unsold()
        self.assertEqual(len(out), 1)
        self.assertFalse(bool(out[0].is_sold))

    def test_get_unsold_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.get_unsold()

    # -----------------------------
    # get_unsold_by_location
    # -----------------------------
    def test_get_unsold_by_location_returns_list(self) -> None:
        now = datetime.utcnow()
        rows = [
            {
                "id": 3,
                "seller_id": 1,
                "title": "Loc",
                "description": "D",
                "image_url": None,
                "price": 2.0,
                "location": "Winnipeg",
                "created_at": now,
                "is_sold": 0,
                "sold_to_id": None,
            }
        ]
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = rows
        self.conn.execute.return_value = exec_result

        out = self.sut.get_unsold_by_location("Win")
        self.assertEqual(len(out), 1)
        self.assertIn("Win", out[0].location)

    def test_get_unsold_by_location_raises_database_query_error_on_sqlalchemy_error(
        self,
    ) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.get_unsold_by_location("Winnipeg")

    # -----------------------------
    # get_unsold_by_max_price
    # -----------------------------
    def test_get_unsold_by_max_price_returns_list(self) -> None:
        now = datetime.utcnow()
        rows = [
            {
                "id": 4,
                "seller_id": 1,
                "title": "Cheap",
                "description": "D",
                "image_url": None,
                "price": 10.0,
                "location": None,
                "created_at": now,
                "is_sold": 0,
                "sold_to_id": None,
            }
        ]
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = rows
        self.conn.execute.return_value = exec_result

        out = self.sut.get_unsold_by_max_price(10.0)
        self.assertEqual(len(out), 1)
        self.assertLessEqual(out[0].price, 10.0)

    def test_get_unsold_by_max_price_raises_database_query_error_on_sqlalchemy_error(
        self,
    ) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.get_unsold_by_max_price(10.0)

    # -----------------------------
    # get_unsold_by_location_and_max_price
    # -----------------------------
    def test_get_unsold_by_location_and_max_price_returns_list(self) -> None:
        now = datetime.utcnow()
        rows = [
            {
                "id": 5,
                "seller_id": 1,
                "title": "Filter",
                "description": "D",
                "image_url": None,
                "price": 20.0,
                "location": "Winnipeg",
                "created_at": now,
                "is_sold": 0,
                "sold_to_id": None,
            }
        ]
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = rows
        self.conn.execute.return_value = exec_result

        out = self.sut.get_unsold_by_location_and_max_price("Win", 25.0)
        self.assertEqual(len(out), 1)
        self.assertLessEqual(out[0].price, 25.0)

    def test_get_unsold_by_location_and_max_price_raises_database_query_error_on_sqlalchemy_error(
        self,
    ) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.get_unsold_by_location_and_max_price("Winnipeg", 25.0)

    # -----------------------------
    # get_recent_unsold
    # -----------------------------
    def test_get_recent_unsold_returns_list(self) -> None:
        now = datetime.utcnow()
        rows = [
            {
                "id": 6,
                "seller_id": 1,
                "title": "Recent",
                "description": "D",
                "image_url": None,
                "price": 1.0,
                "location": None,
                "created_at": now,
                "is_sold": 0,
                "sold_to_id": None,
            }
        ]
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = rows
        self.conn.execute.return_value = exec_result

        out = self.sut.get_recent_unsold(limit=10, offset=0)
        self.assertEqual(len(out), 1)

    def test_get_recent_unsold_raises_database_query_error_on_sqlalchemy_error(
        self,
    ) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.get_recent_unsold(10, 0)

    # -----------------------------
    # find_unsold_by_title_keyword
    # -----------------------------
    def test_find_unsold_by_title_keyword_returns_list(self) -> None:
        now = datetime.utcnow()
        rows = [
            {
                "id": 7,
                "seller_id": 1,
                "title": "Bike rack",
                "description": "D",
                "image_url": None,
                "price": 30.0,
                "location": None,
                "created_at": now,
                "is_sold": 0,
                "sold_to_id": None,
            }
        ]
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = rows
        self.conn.execute.return_value = exec_result

        out = self.sut.find_unsold_by_title_keyword("Bike", limit=10, offset=0)
        self.assertEqual(len(out), 1)
        self.assertIn("Bike", out[0].title)

    def test_find_unsold_by_title_keyword_raises_database_query_error_on_sqlalchemy_error(
        self,
    ) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.find_unsold_by_title_keyword("Bike", 10, 0)

    # -----------------------------
    # update
    # -----------------------------
    def test_update_updates_and_returns_refreshed_listing(self) -> None:
        listing = self._listing(
            listing_id=10, title="New", description="NewD", price=99.0
        )

        # UPDATE call result
        update_result = MagicMock()
        update_result.rowcount = 1

        # After transaction, get_by_id is called: we return a Listing instance
        refreshed = self._listing(
            listing_id=10, title="New", description="NewD", price=99.0
        )

        # conn.execute used once (update)
        self.conn.execute.return_value = update_result

        # patch get_by_id on the SUT to return refreshed
        self.sut.get_by_id = MagicMock(return_value=refreshed)  # type: ignore[method-assign]

        out = self.sut.update(listing)

        self.assertEqual(out, refreshed)
        self.db_util.transaction.assert_called_once()

    def test_update_raises_listing_not_found_when_rowcount_zero(self) -> None:
        listing = self._listing(listing_id=999, title="X", description="Y", price=1.0)

        update_result = MagicMock()
        update_result.rowcount = 0
        self.conn.execute.return_value = update_result

        with self.assertRaises(ListingNotFoundError):
            self.sut.update(listing)

    def test_update_raises_listing_not_found_when_refreshed_none(self) -> None:
        listing = self._listing(listing_id=10, title="X", description="Y", price=1.0)

        update_result = MagicMock()
        update_result.rowcount = 1
        self.conn.execute.return_value = update_result

        self.sut.get_by_id = MagicMock(return_value=None)  # type: ignore[method-assign]

        with self.assertRaises(ListingNotFoundError):
            self.sut.update(listing)

    def test_update_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        listing = self._listing(listing_id=10, title="X", description="Y", price=1.0)
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.update(listing)

    # -----------------------------
    # set_sold
    # -----------------------------
    def test_set_sold_updates_when_row_exists(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 1
        self.conn.execute.return_value = exec_result

        self.sut.set_sold(1, True, 2)

        self.db_util.transaction.assert_called_once()
        self.conn.execute.assert_called_once()

    def test_set_sold_raises_listing_not_found_when_rowcount_zero(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 0
        self.conn.execute.return_value = exec_result

        with self.assertRaises(ListingNotFoundError):
            self.sut.set_sold(999, True, 2)

    def test_set_sold_allows_none_sold_to_id_and_updates(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 1
        self.conn.execute.return_value = exec_result

        self.sut.set_sold(1, False, None)

        self.db_util.transaction.assert_called_once()
        self.conn.execute.assert_called_once()

    def test_set_sold_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.set_sold(1, True, 2)

    # -----------------------------
    # set_price
    # -----------------------------
    def test_set_price_updates_when_row_exists(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 1
        self.conn.execute.return_value = exec_result

        self.sut.set_price(1, 9.99)

        self.db_util.transaction.assert_called_once()
        self.conn.execute.assert_called_once()

    def test_set_price_raises_listing_not_found_when_rowcount_zero(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 0
        self.conn.execute.return_value = exec_result

        with self.assertRaises(ListingNotFoundError):
            self.sut.set_price(999, 9.99)

    def test_set_price_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.set_price(1, 9.99)

    # -----------------------------
    # remove
    # -----------------------------
    def test_remove_returns_true_when_deleted(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 1
        self.conn.execute.return_value = exec_result

        out = self.sut.remove(1)
        self.assertTrue(out)

    def test_remove_returns_false_when_missing(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 0
        self.conn.execute.return_value = exec_result

        out = self.sut.remove(999)
        self.assertFalse(out)

    def test_remove_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.remove(1)
