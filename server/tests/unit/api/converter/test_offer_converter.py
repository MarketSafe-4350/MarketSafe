from __future__ import annotations

import unittest
from datetime import datetime, timezone

from pydantic import ValidationError as PydanticValidationError

from src.api.converter.offer_converter import (
    OfferCreate,
    OfferResponse,
)
from src.domain_models import Offer


class TestOfferConverter(unittest.TestCase):
    # -----------------------------
    # OfferCreate (pydantic validation)
    # -----------------------------
    def test_offer_create_valid(self) -> None:
        dto = OfferCreate(
            offered_price=10.0,
            location_offered="Winnipeg",
        )
        self.assertEqual(dto.offered_price, 10.0)

    def test_offer_create_rejects_non_positive_price(self) -> None:
        with self.assertRaises(PydanticValidationError):
            OfferCreate(offered_price=0)

    def test_offer_create_rejects_location_over_max_length(self) -> None:
        with self.assertRaises(PydanticValidationError):
            OfferCreate(
                offered_price=1.0,
                location_offered="a" * 121,
            )

    # -----------------------------
    # OfferCreate.to_domain
    # -----------------------------
    def test_offer_create_to_domain_sets_fields(self) -> None:
        dto = OfferCreate(
            offered_price=50.5,
            location_offered="Winnipeg",
        )

        out = dto.to_domain(listing_id=7, sender_id=3)

        self.assertIsInstance(out, Offer)
        self.assertEqual(out.listing_id, 7)
        self.assertEqual(out.sender_id, 3)
        self.assertEqual(out.offered_price, 50.5)
        self.assertEqual(out.location_offered, "Winnipeg")

    # -----------------------------
    # OfferResponse.from_domain
    # -----------------------------
    def test_offer_response_from_domain_maps_all_fields_with_created_date(self) -> None:
        created = datetime(2026, 3, 4, 12, 30, 0, tzinfo=timezone.utc)

        offer = Offer(
            listing_id=2,
            sender_id=7,
            offered_price=50.0,
            offer_id=10,
            location_offered="Winnipeg",
            seen=False,
            accepted=None,
            created_date=created,
        )

        out = OfferResponse.from_domain(offer)

        self.assertEqual(out.id, 10)
        self.assertEqual(out.listing_id, 2)
        self.assertEqual(out.sender_id, 7)
        self.assertEqual(out.offered_price, 50.0)
        self.assertEqual(out.location_offered, "Winnipeg")
        self.assertFalse(out.seen)
        self.assertIsNone(out.accepted)
        self.assertEqual(out.created_date, created.isoformat())

    def test_offer_response_from_domain_handles_none_created_date(self) -> None:
        offer = Offer(
            listing_id=7,
            sender_id=3,
            offered_price=1.0,
            offer_id=1,
            location_offered=None,
            seen=True,
            accepted=True,
            created_date=None,
        )

        out = OfferResponse.from_domain(offer)

        self.assertEqual(out.id, 1)
        self.assertIsNone(out.created_date)
        self.assertTrue(out.seen)
