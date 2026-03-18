from __future__ import annotations

import unittest
from pydantic import ValidationError

from src.api.converter.offer_converter import OfferCreate, OfferResponse
from src.domain_models.offer import Offer


class TestOfferConverter(unittest.TestCase):

    # -----------------------------
    # VALIDATION
    # -----------------------------
    def test_offer_create_valid(self):
        dto = OfferCreate(
            offered_price=10.0,
            location_offered="Winnipeg",
        )
        self.assertEqual(dto.offered_price, 10.0)

    def test_offer_create_invalid_price(self):
        with self.assertRaises(ValidationError):
            OfferCreate(offered_price=-1)

    # -----------------------------
    # TO DOMAIN
    # -----------------------------
    def test_to_domain(self):
        dto = OfferCreate(
            offered_price=20.0,
            location_offered="WPG",
        )

        result = dto.to_domain(listing_id=1, sender_id=2)

        self.assertIsInstance(result, Offer)
        self.assertEqual(result.listing_id, 1)
        self.assertEqual(result.sender_id, 2)
        self.assertEqual(result.offered_price, 20.0)

    # -----------------------------
    # FROM DOMAIN
    # -----------------------------
    def test_from_domain(self):
        offer = Offer(
            offer_id=1,
            listing_id=2,
            sender_id=3,
            offered_price=50.0,
            location_offered="WPG",
        )

        out = OfferResponse.from_domain(offer)

        self.assertEqual(out.id, 1)
        self.assertEqual(out.listing_id, 2)
        self.assertEqual(out.sender_id, 3)
        self.assertEqual(out.offered_price, 50.0)