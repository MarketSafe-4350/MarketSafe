from __future__ import annotations

import unittest
from datetime import datetime
from unittest.mock import MagicMock

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.db import DBUtility
from src.domain_models import Offer
from src.utils import DatabaseQueryError, OfferNotFoundError
from src.db.offer.mysql.mysql_offer_db import MySQLOfferDB


class TestMySQLOfferDB(unittest.TestCase):
    def setUp(self) -> None:
        self.db_util: MagicMock = MagicMock(spec=DBUtility)
        self.sut = MySQLOfferDB(self.db_util)

        self.conn: MagicMock = MagicMock()

        self.connect_cm: MagicMock = MagicMock()
        self.connect_cm.__enter__.return_value = self.conn
        self.connect_cm.__exit__.return_value = False

        self.tx_cm: MagicMock = MagicMock()
        self.tx_cm.__enter__.return_value = self.conn
        self.tx_cm.__exit__.return_value = False

        self.db_util.connect.return_value = self.connect_cm
        self.db_util.transaction.return_value = self.tx_cm

    def _offer(
        self,
        *,
        offer_id: int | None = None,
        listing_id: int = 1,
        sender_id: int = 2,
        offered_price: float = 50.0,
        location_offered: str | None = "Winnipeg",
        seen: bool = False,
        accepted: bool | None = None,
    ) -> Offer:
        return Offer(
            offer_id=offer_id,
            listing_id=listing_id,
            sender_id=sender_id,
            offered_price=offered_price,
            location_offered=location_offered,
            seen=seen,
            accepted=accepted,
        )

    def _row(
        self,
        *,
        offer_id: int = 1,
        listing_id: int = 1,
        sender_id: int = 2,
        offered_price: float = 50.0,
        location_offered: str | None = "Winnipeg",
        created_date: datetime | None = None,
        seen: bool = False,
        accepted: bool | None = None,
    ) -> dict:
        return {
            "id": offer_id,
            "listing_id": listing_id,
            "sender_id": sender_id,
            "offered_price": offered_price,
            "location_offered": location_offered,
            "created_date": created_date or datetime.utcnow(),
            "seen": seen,
            "accepted": accepted,
        }

    # -----------------------------
    # add
    # -----------------------------
    def test_add_inserts_and_returns_offer_with_new_id(self) -> None:
        offer = self._offer(listing_id=1, sender_id=2, offered_price=75.0)

        exec_result = MagicMock()
        exec_result.lastrowid = 42
        self.conn.execute.return_value = exec_result

        out = self.sut.add(offer)

        self.db_util.transaction.assert_called_once()
        self.conn.execute.assert_called_once()
        self.assertEqual(out.id, 42)
        self.assertEqual(out.listing_id, 1)
        self.assertEqual(out.sender_id, 2)
        self.assertEqual(out.offered_price, 75.0)

    def test_add_raises_database_query_error_on_integrity_error(self) -> None:
        offer = self._offer()
        self.conn.execute.side_effect = IntegrityError("stmt", {}, Exception("fk"))

        with self.assertRaises(DatabaseQueryError):
            self.sut.add(offer)

    def test_add_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        offer = self._offer()
        self.conn.execute.side_effect = SQLAlchemyError("boom")

        with self.assertRaises(DatabaseQueryError):
            self.sut.add(offer)

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

    def test_get_by_id_returns_offer_when_found(self) -> None:
        row = self._row(offer_id=5, listing_id=1, sender_id=2, offered_price=50.0)
        exec_result = MagicMock()
        exec_result.mappings.return_value.first.return_value = row
        self.conn.execute.return_value = exec_result

        out = self.sut.get_by_id(5)
        self.assertIsNotNone(out)
        self.assertEqual(out.id, 5)
        self.assertEqual(out.listing_id, 1)
        self.assertEqual(out.sender_id, 2)
        self.assertEqual(out.offered_price, 50.0)

    def test_get_by_id_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.get_by_id(1)

    # -----------------------------
    # get_all
    # -----------------------------
    def test_get_all_returns_list(self) -> None:
        rows = [
            self._row(offer_id=1, listing_id=1, sender_id=2),
            self._row(offer_id=2, listing_id=1, sender_id=3),
        ]
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = rows
        self.conn.execute.return_value = exec_result

        out = self.sut.get_all()
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0].id, 1)
        self.assertEqual(out[1].id, 2)

    def test_get_all_returns_empty_list_when_no_offers(self) -> None:
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = []
        self.conn.execute.return_value = exec_result

        out = self.sut.get_all()
        self.assertEqual(out, [])

    def test_get_all_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.get_all()

    # -----------------------------
    # get_by_listing_id
    # -----------------------------
    def test_get_by_listing_id_returns_list(self) -> None:
        rows = [
            self._row(offer_id=10, listing_id=7, sender_id=2),
            self._row(offer_id=11, listing_id=7, sender_id=3),
        ]
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = rows
        self.conn.execute.return_value = exec_result

        out = self.sut.get_by_listing_id(7)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0].listing_id, 7)
        self.assertEqual(out[1].listing_id, 7)

    def test_get_by_listing_id_returns_empty_list_when_none(self) -> None:
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = []
        self.conn.execute.return_value = exec_result

        out = self.sut.get_by_listing_id(99)
        self.assertEqual(out, [])

    def test_get_by_listing_id_raises_database_query_error_on_sqlalchemy_error(
        self,
    ) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.get_by_listing_id(1)

    # -----------------------------
    # get_by_sender_id
    # -----------------------------
    def test_get_by_sender_id_returns_list(self) -> None:
        rows = [self._row(offer_id=20, listing_id=1, sender_id=5)]
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = rows
        self.conn.execute.return_value = exec_result

        out = self.sut.get_by_sender_id(5)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].sender_id, 5)

    def test_get_by_sender_id_returns_empty_list_when_none(self) -> None:
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = []
        self.conn.execute.return_value = exec_result

        out = self.sut.get_by_sender_id(99)
        self.assertEqual(out, [])

    def test_get_by_sender_id_raises_database_query_error_on_sqlalchemy_error(
        self,
    ) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.get_by_sender_id(1)

    # -----------------------------
    # get_accepted_by_listing_id
    # -----------------------------
    def test_get_accepted_by_listing_id_returns_accepted_offers(self) -> None:
        rows = [self._row(offer_id=30, listing_id=3, accepted=True)]
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = rows
        self.conn.execute.return_value = exec_result

        out = self.sut.get_accepted_by_listing_id(3)
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].accepted)

    def test_get_accepted_by_listing_id_returns_empty_list_when_none(self) -> None:
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = []
        self.conn.execute.return_value = exec_result

        out = self.sut.get_accepted_by_listing_id(3)
        self.assertEqual(out, [])

    def test_get_accepted_by_listing_id_raises_database_query_error_on_sqlalchemy_error(
        self,
    ) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.get_accepted_by_listing_id(1)

    # -----------------------------
    # get_unseen_by_listing_id
    # -----------------------------
    def test_get_unseen_by_listing_id_returns_unseen_offers(self) -> None:
        rows = [self._row(offer_id=40, listing_id=4, seen=False)]
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = rows
        self.conn.execute.return_value = exec_result

        out = self.sut.get_unseen_by_listing_id(4)
        self.assertEqual(len(out), 1)
        self.assertFalse(out[0].seen)

    def test_get_unseen_by_listing_id_returns_empty_list_when_none(self) -> None:
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = []
        self.conn.execute.return_value = exec_result

        out = self.sut.get_unseen_by_listing_id(4)
        self.assertEqual(out, [])

    def test_get_unseen_by_listing_id_raises_database_query_error_on_sqlalchemy_error(
        self,
    ) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.get_unseen_by_listing_id(1)

    # -----------------------------
    # get_pending_by_listing_id
    # -----------------------------
    def test_get_pending_by_listing_id_returns_pending_offers(self) -> None:
        rows = [self._row(offer_id=50, listing_id=5, accepted=None)]
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = rows
        self.conn.execute.return_value = exec_result

        out = self.sut.get_pending_by_listing_id(5)
        self.assertEqual(len(out), 1)
        self.assertIsNone(out[0].accepted)

    def test_get_pending_by_listing_id_returns_empty_list_when_none(self) -> None:
        exec_result = MagicMock()
        exec_result.mappings.return_value.all.return_value = []
        self.conn.execute.return_value = exec_result

        out = self.sut.get_pending_by_listing_id(5)
        self.assertEqual(out, [])

    def test_get_pending_by_listing_id_raises_database_query_error_on_sqlalchemy_error(
        self,
    ) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.get_pending_by_listing_id(1)

    # -----------------------------
    # get_by_sender_and_listing
    # -----------------------------
    def test_get_by_sender_and_listing_returns_offer_when_found(self) -> None:
        row = self._row(offer_id=60, listing_id=2, sender_id=3)
        exec_result = MagicMock()
        exec_result.mappings.return_value.first.return_value = row
        self.conn.execute.return_value = exec_result

        out = self.sut.get_by_sender_and_listing(sender_id=3, listing_id=2)
        self.assertIsNotNone(out)
        self.assertEqual(out.id, 60)
        self.assertEqual(out.sender_id, 3)
        self.assertEqual(out.listing_id, 2)

    def test_get_by_sender_and_listing_returns_none_when_missing(self) -> None:
        exec_result = MagicMock()
        exec_result.mappings.return_value.first.return_value = None
        self.conn.execute.return_value = exec_result

        out = self.sut.get_by_sender_and_listing(sender_id=99, listing_id=99)
        self.assertIsNone(out)

    def test_get_by_sender_and_listing_raises_database_query_error_on_sqlalchemy_error(
        self,
    ) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.get_by_sender_and_listing(1, 1)

    # -----------------------------
    # set_seen
    # -----------------------------
    def test_set_seen_updates_when_row_exists(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 1
        self.conn.execute.return_value = exec_result

        self.sut.set_seen(1)

        self.db_util.transaction.assert_called_once()
        self.conn.execute.assert_called_once()

    def test_set_seen_raises_offer_not_found_when_rowcount_zero(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 0
        self.conn.execute.return_value = exec_result

        with self.assertRaises(OfferNotFoundError):
            self.sut.set_seen(999)

    def test_set_seen_raises_database_query_error_on_sqlalchemy_error(self) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.set_seen(1)

    # -----------------------------
    # set_accepted
    # -----------------------------
    def test_set_accepted_true_updates_when_row_exists(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 1
        self.conn.execute.return_value = exec_result

        self.sut.set_accepted(1, True)

        self.db_util.transaction.assert_called_once()
        self.conn.execute.assert_called_once()

    def test_set_accepted_false_updates_when_row_exists(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 1
        self.conn.execute.return_value = exec_result

        self.sut.set_accepted(1, False)

        self.db_util.transaction.assert_called_once()
        self.conn.execute.assert_called_once()

    def test_set_accepted_raises_offer_not_found_when_rowcount_zero(self) -> None:
        exec_result = MagicMock()
        exec_result.rowcount = 0
        self.conn.execute.return_value = exec_result

        with self.assertRaises(OfferNotFoundError):
            self.sut.set_accepted(999, True)

    def test_set_accepted_raises_database_query_error_on_sqlalchemy_error(
        self,
    ) -> None:
        self.conn.execute.side_effect = SQLAlchemyError("fail")

        with self.assertRaises(DatabaseQueryError):
            self.sut.set_accepted(1, True)

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
