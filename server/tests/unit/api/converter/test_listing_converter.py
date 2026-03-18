from __future__ import annotations
from unittest.mock import Mock

import unittest
from datetime import datetime, timezone

from pydantic import ValidationError as PydanticValidationError

from src.api.converter.listing_converter import (
    ListingCreate,
    ListingResponse,
)
from src.domain_models import Listing


class TestListingConverter(unittest.TestCase):
    # -----------------------------
    # ListingCreate (pydantic validation)
    # -----------------------------
    def test_listing_create_valid(self) -> None:
        dto = ListingCreate(
            title="Bike",
            description="Nice bike",
            price=10.0,
            image_url="http://img",
            location="Winnipeg",
        )
        self.assertEqual(dto.title, "Bike")

    def test_listing_create_rejects_non_positive_price(self) -> None:
        with self.assertRaises(PydanticValidationError):
            ListingCreate(title="X", description="Y", price=0)

    def test_listing_create_rejects_too_large_price(self) -> None:
        with self.assertRaises(PydanticValidationError):
            ListingCreate(title="X", description="Y", price=100_000_000.00)

    def test_listing_create_rejects_location_over_max_length(self) -> None:
        with self.assertRaises(PydanticValidationError):
            ListingCreate(
                title="X",
                description="Y",
                price=1.0,
                location="a" * 121,
            )

    # -----------------------------
    # ListingCreate.to_domain
    # -----------------------------
    def test_listing_create_to_domain_sets_fields(self) -> None:
        dto = ListingCreate(
            title="Bike",
            description="Nice",
            price=50.5,
            image_url=None,
            location="Winnipeg",
        )

        out = dto.to_domain(seller_id=7)

        self.assertIsInstance(out, Listing)
        self.assertEqual(out.seller_id, 7)
        self.assertEqual(out.title, "Bike")
        self.assertEqual(out.description, "Nice")
        self.assertEqual(out.price, 50.5)
        self.assertIsNone(out.image_url)
        self.assertEqual(out.location, "Winnipeg")

    # -----------------------------
    # ListingResponse.from_domain
    # -----------------------------
    def test_listing_response_from_domain_maps_all_fields_with_created_at(self) -> None:
        created = datetime(2026, 3, 4, 12, 30, 0, tzinfo=timezone.utc)

        listing = Listing(
            listing_id=10,
            seller_id=7,
            title="Bike",
            description="Nice",
            price=50.0,
            image_url="http://img",
            location="Winnipeg",
            created_at=created,
            is_sold=False,
            sold_to_id=None,
        )

        out = ListingResponse.from_domain(listing)

        self.assertEqual(out.id, 10)
        self.assertEqual(out.seller_id, 7)
        self.assertEqual(out.title, "Bike")
        self.assertEqual(out.description, "Nice")
        self.assertEqual(out.price, 50.0)
        self.assertEqual(out.image_url, "http://img")
        self.assertEqual(out.location, "Winnipeg")
        self.assertEqual(out.created_at, created.isoformat())
        self.assertFalse(out.is_sold)

    def test_listing_response_from_domain_handles_none_created_at(self) -> None:
        listing = Listing(
            listing_id=1,
            seller_id=7,
            title="X",
            description="Y",
            price=1.0,
            image_url=None,
            location=None,
            created_at=None,
            is_sold=True,
            sold_to_id=99,
        )

        out = ListingResponse.from_domain(listing)

        self.assertEqual(out.id, 1)
        self.assertIsNone(out.created_at)
        self.assertTrue(out.is_sold)

    def test_listing_response_from_domain_uses_media_storage_public_url(self) -> None:
        listing = Listing(
            listing_id=11,
            seller_id=7,
            title="Bike",
            description="Nice",
            price=50.0,
            image_url="listing-images/bike.png",
            location="Winnipeg",
            created_at=None,
            is_sold=False,
            sold_to_id=None,
        )

        media_storage = Mock()
        media_storage.public_url.return_value = (
            "http://localhost:9000/listing-images/bike.png"
        )

        out = ListingResponse.from_domain(
            listing=listing,
            media_storage=media_storage,
        )

        media_storage.public_url.assert_called_once_with("listing-images/bike.png")
        self.assertEqual(
            out.image_url,
            "http://localhost:9000/listing-images/bike.png",
        )
