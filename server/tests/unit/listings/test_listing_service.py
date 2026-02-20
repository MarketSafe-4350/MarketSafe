import unittest
from unittest.mock import MagicMock

from src.business_logic.services.listing_service import ListingService
from src.domain_models.listing import Listing
from src.utils import ValidationError


class TestListingService(unittest.TestCase):
    def setUp(self) -> None:
        self.manager: MagicMock = MagicMock()
        self.service = ListingService(self.manager)

    # -----------------------------
    # create_listing - happy path
    # -----------------------------
    def test_create_listing_validates_and_delegates_to_manager(self) -> None:
        result = Listing(
            listing_id=123,
            seller_id=456,
            title="Test Listing",
            description="This is a test listing.",
            price=10.0,
            location="Test Location",
            image_url="http://example.com/image.jpg",
        )

        self.manager.create_listing.return_value = result

        # Currently, service does NOT call manager (it's commented out)
        self.manager.create_listing.assert_not_called()

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

        # Since validation failed, should NOT call manager
        self.manager.create_listing.assert_not_called()

    # -----------------------------
    # create_listing - title validation
    # -----------------------------
    def test_create_listing_title_none_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self.service.create_listing(
                seller_id=456,
                title=None,  # invalid
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
                title="   ",  # invalid - empty string with whitespace
                description="Valid description",
                price=10.0,
                location="Valid location",
                image_url=None,
            )

        errors = ctx.exception.details["errors"]
        self.assertIn("title", errors)
        self.assertIn("Title cannot be empty or whitespace only.", errors["title"])

        self.manager.create_listing.assert_not_called()

    # -----------------------------
    # create_listing - description validation
    # -----------------------------
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
                description="",  # invalid - empty string
                price=10.0,
                location="Valid location",
                image_url=None,
            )

        errors = ctx.exception.details["errors"]
        self.assertIn("description", errors)
        self.assertIn("Description cannot be empty.", errors["description"])

        self.manager.create_listing.assert_not_called()

    # -----------------------------
    # create_listing - price validation
    # -----------------------------
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

    # -----------------------------
    # create_listing - location validation
    # -----------------------------
    def test_create_listing_location_empty_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self.service.create_listing(
                seller_id=1,
                title="A",
                description="B",
                price=10.0,
                location="",  # invalid
                image_url=None,
            )

        errors = ctx.exception.details["errors"]
        self.assertIn("location", errors)

        self.assertIn("Location cannot be empty.", errors["location"])

        self.manager.create_listing.assert_not_called()

    # -----------------------------
    # create_listing - image URL validation
    # -----------------------------
    def test_create_listing_image_url_valid(self) -> None:
        result = self.service.create_listing(
            seller_id=1,
            title="A",
            description="B",
            price=10.0,
            location="Winnipeg",
            image_url="http://example.com/image.jpg",  # valid
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.image_url, "http://example.com/image.jpg")
        self.assertEqual(result.title, "A")
        self.assertEqual(result.price, 10.0)

        self.manager.create_listing.assert_not_called()

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
                image_url="ftp://example.com/image.jpg",  # invalid scheme
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
                image_url="   ",  # invalid - empty string with whitespace
            )

        errors = ctx.exception.details["errors"]
        self.assertIn("image_url", errors)

        self.assertIn("Image URL cannot be empty if provided.", errors["image_url"])

        self.manager.create_listing.assert_not_called()

    def test_create_listing_image_url_none_is_valid(self) -> None:
        result = self.service.create_listing(
            seller_id=1,
            title="A",
            description="B",
            price=10.0,
            location="Winnipeg",
            image_url=None,  # valid - indicates no image provided
        )

        # Should not raise exception
        self.assertIsNotNone(result)
        self.assertIsNone(result.image_url)
        self.assertEqual(result.title, "A")
        self.assertEqual(result.price, 10.0)

        self.manager.create_listing.assert_not_called()

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
