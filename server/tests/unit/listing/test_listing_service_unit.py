import unittest
from unittest.mock import MagicMock
from typing import List
from datetime import datetime, timezone

from src.business_logic.services.listing_service import ListingService
from src.domain_models.listing import Listing
from src.utils import ValidationError, ListingNotFoundError, UnapprovedBehaviorError


class TestListingServiceUnit(unittest.TestCase):
    def setUp(self) -> None:
        self.manager: MagicMock = MagicMock()
        self.service = ListingService(listing_manager=self.manager)

    def test_get_all_listing_delegates_to_manager(self) -> None:
        one_listing = Listing(
            listing_id=123,
            seller_id=456,
            title="Test Listing",
            description="This is a test listing.",
            price=10.0,
            location="Test Location",
            image_url="http://example.com/image.jpg",
        )
        expected_result: List[Listing] = [one_listing, one_listing]

        self.manager.list_listings.return_value = expected_result
        result = self.service.get_all_listing()
        self.manager.list_listings.assert_called_once()
        self.assertEqual(result, expected_result)

    # -----------------------------
    # get listing by user id
    # -----------------------------
    def test_get_listing_by_user_id_delegates_to_manager(self) -> None:
        user_id = 456
        one_listing = Listing(
            listing_id=123,
            seller_id=user_id,
            title="Test Listing",
            description="This is a test listing.",
            price=10.0,
            location="Test Location",
            image_url="http://example.com/image.jpg",
        )
        expected_result: List[Listing] = [one_listing, one_listing]

        self.manager.list_listings_by_seller.return_value = expected_result
        result = self.service.get_listing_by_user_id(user_id=user_id)
        self.manager.list_listings_by_seller.assert_called_once()
        self.assertEqual(result, expected_result)

    def test_search_listings_filters_and_ranks_relevant_results(self) -> None:
        laptop_title_match = Listing(
            listing_id=1,
            seller_id=10,
            title="Gaming Laptop",
            description="Powerful and clean",
            price=900.0,
            location="Winnipeg",
            image_url=None,
            created_at=datetime(2026, 2, 25, tzinfo=timezone.utc),
        )

        laptop_description_match = Listing(
            listing_id=2,
            seller_id=11,
            title="Desktop PC",
            description="Includes laptop bag and monitor",
            price=700.0,
            location="Winnipeg",
            image_url=None,
            created_at=datetime(2026, 2, 24, tzinfo=timezone.utc),
        )

        unrelated = Listing(
            listing_id=3,
            seller_id=12,
            title="Bike",
            description="Mountain bike",
            price=300.0,
            location="Brandon",
            image_url=None,
            created_at=datetime(2026, 2, 23, tzinfo=timezone.utc),
        )

        self.manager.list_listings.return_value = [
            unrelated,
            laptop_description_match,
            laptop_title_match,
        ]

        result = self.service.search_listings("laptop")

        self.assertEqual([listing.id for listing in result], [1, 2])
        self.manager.list_listings.assert_called_once()

    def test_search_listings_blank_query_returns_empty_list(self) -> None:
        result = self.service.search_listings("   ")
        self.assertEqual(result, [])
        self.manager.list_listings.assert_not_called()

    # -----------------------------
    # create_listing - happy path
    # -----------------------------
    def test_create_listing_validates_and_delegates_to_manager(self) -> None:
        expected_result: Listing = Listing(
            listing_id=123,
            seller_id=456,
            title="Test Listing",
            description="This is a test listing.",
            price=10.0,
            location="Test Location",
            image_url="http://example.com/image.jpg",
        )

        self.manager.create_listing.return_value = expected_result

        result = self.service.create_listing(
            expected_result.seller_id,
            expected_result.title,
            expected_result.description,
            expected_result.price,
            expected_result.location,
            expected_result.image_url,
        )

        self.manager.create_listing.assert_called_once()

        self.assertIsInstance(result, Listing)
        self.assertEqual(result.seller_id, 456)
        self.assertEqual(result.title, "Test Listing")
        self.assertEqual(result.description, "This is a test listing.")
        self.assertEqual(result.price, 10.0)
        self.assertEqual(result.location, "Test Location")
        self.assertEqual(result.image_url, "http://example.com/image.jpg")
        self.assertFalse(result.is_sold)

    # -----------------------------
    # create_listing - validation errors
    # -----------------------------
    def test_create_listing_all_invalid_fields_raises_validation_error(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self.service.create_listing(
                seller_id=456,
                title="   ",  # invalid
                description="",  # invalid
                price=None,  # invalid
                location="",  # invalid
                image_url="ftp://x.com/a",  # invalid scheme
            )

        err = ctx.exception
        self.assertEqual(err.code, "VALIDATION_ERROR")
        self.assertEqual(err.status_code, 422)
        self.assertIsNotNone(err.details)
        self.assertIn("errors", err.details)

        errors = err.details["errors"]
        self.assertIn("title", errors)
        self.assertIn("description", errors)
        self.assertIn("price", errors)
        self.assertIn("location", errors)
        self.assertIn("image_url", errors)


        self.manager.create_listing.assert_not_called()


    def test_create_listing_title_none_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self.service.create_listing(
                seller_id=456,
                title=None, 
                description="Valid description",
                price=10.0,
                location="Valid location",
                image_url=None,
            )

        errors = ctx.exception.details["errors"]
        self.assertIn("title", errors)
        self.assertIn("Title cannot be empty or whitespace only.", errors["title"])

        self.manager.create_listing.assert_not_called()

    def test_create_listing_title_empty_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self.service.create_listing(
                seller_id=456,
                title="   ",
                description="Valid description",
                price=10.0,
                location="Valid location",
                image_url=None,
            )

        errors = ctx.exception.details["errors"]
        self.assertIn("title", errors)
        self.assertIn("Title cannot be empty or whitespace only.", errors["title"])

        self.manager.create_listing.assert_not_called()


    def test_create_listing_description_none_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self.service.create_listing(
                seller_id=456,
                title="Valid title",
                description=None,  # invalid
                price=10.0,
                location="Valid location",
                image_url=None,
            )

        errors = ctx.exception.details["errors"]
        self.assertIn("description", errors)
        self.assertIn("Description cannot be empty.", errors["description"])

        self.manager.create_listing.assert_not_called()

    def test_create_listing_description_empty_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self.service.create_listing(
                seller_id=456,
                title="Valid title",
                description="", 
                price=10.0,
                location="Valid location",
                image_url=None,
            )

        errors = ctx.exception.details["errors"]
        self.assertIn("description", errors)
        self.assertIn("Description cannot be empty.", errors["description"])

        self.manager.create_listing.assert_not_called()


    def test_create_listing_price_less_zero_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self.service.create_listing(
                seller_id=1,
                title="A",
                description="B",
                price=-1.0,
                location="Winnipeg",
                image_url=None,
            )

        errors = ctx.exception.details["errors"]
        self.assertIn("price", errors)

        self.assertIn("Price must be a non-negative number.", errors["price"])

        self.manager.create_listing.assert_not_called()

    def test_create_listing_price_none_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self.service.create_listing(
                seller_id=1,
                title="A",
                description="B",
                price=None,
                location="Winnipeg",
                image_url=None,
            )

        errors = ctx.exception.details["errors"]
        self.assertIn("price", errors)

        self.assertIn("Price cannot be None.", errors["price"])

        self.manager.create_listing.assert_not_called()


    def test_create_listing_location_empty_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self.service.create_listing(
                seller_id=1,
                title="A",
                description="B",
                price=10.0,
                location="", 
                image_url=None,
            )

        errors = ctx.exception.details["errors"]
        self.assertIn("location", errors)

        self.assertIn("Location cannot be empty.", errors["location"])

        self.manager.create_listing.assert_not_called()


    def test_create_listing_image_url_valid(self) -> None:
        expected = Listing(
            listing_id=123,
            seller_id=1,
            title="A",
            description="B",
            price=10.0,
            location="Winnipeg",
            image_url="http://example.com/image.jpg",
        )

        self.manager.create_listing.return_value = expected

        result = self.service.create_listing(
            seller_id=1,
            title="A",
            description="B",
            price=10.0,
            location="Winnipeg",
            image_url="http://example.com/image.jpg",
        )

        # manager should be called once
        self.manager.create_listing.assert_called_once()

        self.assertIsNotNone(result)
        self.assertEqual(result.id, 123)
        self.assertEqual(result.image_url, "http://example.com/image.jpg")
        self.assertEqual(result.title, "A")
        self.assertEqual(result.price, 10.0)

    def test_create_listing_image_url_invalid_scheme_raises_validation_error(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self.service.create_listing(
                seller_id=1,
                title="A",
                description="B",
                price=10.0,
                location="Winnipeg",
                image_url="ftp://example.com/image.jpg",
            )

        errors = ctx.exception.details["errors"]
        self.assertIn("image_url", errors)

        self.assertIn(
            "Image URL must start with http:// or https://", errors["image_url"]
        )

        self.manager.create_listing.assert_not_called()

    def test_create_listing_image_url_empty_raises_validation_error(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self.service.create_listing(
                seller_id=1,
                title="A",
                description="B",
                price=10.0,
                location="Winnipeg",
                image_url="   ", 
            )

        errors = ctx.exception.details["errors"]
        self.assertIn("image_url", errors)

        self.assertIn("Image URL cannot be empty if provided.", errors["image_url"])

        self.manager.create_listing.assert_not_called()

    def test_create_listing_image_url_none_is_valid(self) -> None:
        expected_result: Listing = Listing(
            listing_id=123,
            seller_id=456,
            title="Test Listing",
            description="This is a test listing.",
            price=10.0,
            location="Test Location",
            image_url=None,
        )

        self.manager.create_listing.return_value = expected_result

        result = self.service.create_listing(
            seller_id=expected_result.seller_id,
            title=expected_result.title,
            description=expected_result.description,
            price=expected_result.price,
            location=expected_result.location,
            image_url=expected_result.image_url,
        )

        self.manager.create_listing.assert_called_once()
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 123)
        self.assertIsNone(result.image_url)
        self.assertEqual(result.title, "Test Listing")
        self.assertEqual(result.price, 10.0)


    def test_create_listing_image_url_invalid_domain_raises_validation_error(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self.service.create_listing(
                seller_id=1,
                title="A",
                description="B",
                price=10.0,
                location="Winnipeg",
                image_url="http://",  # invalid - missing domain
            )

        errors = ctx.exception.details["errors"]
        self.assertIn("image_url", errors)

        self.assertIn("Image URL must have a valid domain.", errors["image_url"])

        self.manager.create_listing.assert_not_called()


    def test_get_listing_by_id_delegates_and_returns_value(self):
        listing = MagicMock()
        self.manager.get_listing_by_id.return_value = listing
        result = self.service.get_listing_by_id(123)
        self.manager.get_listing_by_id.assert_called_once_with(123)
        self.assertIs(result, listing)


    def test_search_listings_query_none_returns_empty_list(self):
        result = self.service.search_listings(None)
        self.assertEqual(result, [])
        self.manager.list_listings.assert_not_called()


    def test_validate_image_url_local_path_allowed(self):
        errors = {}
        path = "/uploads/listings/abc.png"
        result = self.service._validate_image_url(path, errors)
        self.assertEqual(result, path)
        self.assertEqual(errors, {})
    
    # test delete listing

    def test_delete_listing_not_found_raises(self):
        self.manager.get_listing_by_id.return_value = None

        with self.assertRaises(ListingNotFoundError):
            self.service.delete_listing(listing_id=1, actor_user_id=10)

        self.manager.delete_listing.assert_not_called()

    def test_delete_listing_wrong_actor_raises(self):
        listing = MagicMock()
        listing.seller_id = 999
        self.manager.get_listing_by_id.return_value = listing

        with self.assertRaises(UnapprovedBehaviorError):
            self.service.delete_listing(listing_id=1, actor_user_id=10)

        self.manager.delete_listing.assert_not_called()

    def test_delete_listing_happy_path_delegates(self):
        listing = MagicMock()
        listing.seller_id = 10
        self.manager.get_listing_by_id.return_value = listing
        self.manager.delete_listing.return_value = True

        result = self.service.delete_listing(listing_id=1, actor_user_id=10)

        self.assertTrue(result)
        self.manager.get_listing_by_id.assert_called_once_with(1)
        self.manager.delete_listing.assert_called_once_with(1)