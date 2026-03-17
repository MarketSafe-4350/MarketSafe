from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from src.db import DBUtility
from src.domain_models import Offer
from src.db.offer import OfferDB


class _OfferDBCoverageShim(OfferDB):
    def add(self, offer: Offer) -> Offer:
        return OfferDB.add(self, offer)

    def get_by_id(self, offer_id: int):
        return OfferDB.get_by_id(self, offer_id)

    def get_all(self):
        return OfferDB.get_all(self)

    def get_by_listing_id(self, listing_id: int):
        return OfferDB.get_by_listing_id(self, listing_id)

    def get_by_sender_id(self, sender_id: int):
        return OfferDB.get_by_sender_id(self, sender_id)

    def get_accepted_by_listing_id(self, listing_id: int):
        return OfferDB.get_accepted_by_listing_id(self, listing_id)

    def get_unseen_by_listing_id(self, listing_id: int):
        return OfferDB.get_unseen_by_listing_id(self, listing_id)

    def get_pending_by_listing_id(self, listing_id: int):
        return OfferDB.get_pending_by_listing_id(self, listing_id)

    def get_by_sender_and_listing(self, sender_id: int, listing_id: int):
        return OfferDB.get_by_sender_and_listing(self, sender_id, listing_id)

    def set_seen(self, offer_id: int) -> None:
        return OfferDB.set_seen(self, offer_id)

    def set_accepted(self, offer_id: int, accepted: bool) -> None:
        return OfferDB.set_accepted(self, offer_id, accepted)

    def remove(self, offer_id: int) -> bool:
        return OfferDB.remove(self, offer_id)


class TestOfferDBABC(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock(spec=DBUtility)
        self.sut = _OfferDBCoverageShim(self.db)

        self.sample_offer = Offer(
            listing_id=1,
            sender_id=2,
            offered_price=50.0,
            location_offered="Winnipeg",
        )

    # -----------------------------
    # __init__
    # -----------------------------
    def test_init_stores_db(self) -> None:
        self.assertIs(self.sut._db, self.db)

    # -----------------------------
    # CREATE
    # -----------------------------
    def test_add_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.add(self.sample_offer)

    # -----------------------------
    # READ
    # -----------------------------
    def test_get_by_id_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_by_id(1)

    def test_get_all_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_all()

    def test_get_by_listing_id_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_by_listing_id(1)

    def test_get_by_sender_id_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_by_sender_id(2)

    def test_get_accepted_by_listing_id_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_accepted_by_listing_id(1)

    def test_get_unseen_by_listing_id_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_unseen_by_listing_id(1)

    def test_get_pending_by_listing_id_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_pending_by_listing_id(1)

    def test_get_by_sender_and_listing_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.get_by_sender_and_listing(2, 1)

    # -----------------------------
    # UPDATE
    # -----------------------------
    def test_set_seen_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.set_seen(1)

    def test_set_accepted_true_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.set_accepted(1, True)

    def test_set_accepted_false_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.set_accepted(1, False)

    # -----------------------------
    # DELETE
    # -----------------------------
    def test_remove_raises_not_implemented_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.sut.remove(1)
