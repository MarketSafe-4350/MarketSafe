from src.domain_models.listing import Listing
from src.utils.errors import ValidationError, DatabaseUnavailableError
from urllib.parse import urlparse
from typing import List


class ListingService:
    """Service class for handling listing-related business logic."""

    def __init__(self, listing_manager):
        self.listing_manager = listing_manager

    def get_all_listing(self) -> List[Listing]:
        # test data, waiting for account manager to be created
        listing = Listing(
            seller_id=1,
            title="test title",
            description="test_desc",
            price=1,
            location="test_loc",
            image_url="test_img_url",
        )

        listings: List[Listing] = [listing, listing]
        return listings

    def create_listing(
        self,
        seller_id: int,
        title: str,
        description: str,
        price: float,
        location: str,
        image_url: str | None,
    ) -> Listing:
        """Creates a new listing with the provided details.
           Validates provided details before creating listing.

        Args:
            title (str): The title of the listing.
            description (str): The description of the listing.
            price (float): The price of the listing.
            location (str): The location of the listing.
            image_url (str | None): The image URL for the listing.

        Returns:
            Listing: The newly created listing domain model.
        """
        title, description, price, location, image_url = self._validate_listing(
            title, description, price, location, image_url
        )

        listing = Listing(
            seller_id=seller_id,
            title=title,
            description=description,
            price=price,
            location=location,
            image_url=image_url,
        )

        # created = self.listing_manager.create_listing(listing)
        # return created if created is not None else listing

        # waiting for manager to be implemented, for now just return the listing (after validation)
        return listing

    def _validate_listing(
        self,
        title: str,
        description: str,
        price: float,
        location: str,
        image_url: str | None,
    ):
        """Validates created listing information

        Args:
            title (str): The title of the listing - passed from create_listing.
            description (str): The description of the listing - passed from create_listing.
            price (float): The price of the listing - passed from create_listing.
            location (str): The location of the listing - passed from create_listing.
            image_url (str | None): The image URL for the listing - passed from create_listing.

        Returns:
            title, description, price, location, image_url - All validated from utils/validation.py and self methods

        Raises:
            ValidationError: If any input fails validation checks.

        Note:
            Error handling is done in the route layer (under ./errors/exception_handlers.py),
            so we can raise exceptions here and let the route handle it.
        """
        # Collect all validation errors in a dictionary to return all at once
        # Key is the field name, value is a list of error messages for that field
        errors: dict[str, list[str]] = {}

        title = self._validate_title(title, errors=errors)
        description = self._validate_description(description, errors=errors)
        price = self._validate_price(price, errors=errors)
        location = self._validate_location(location, errors=errors)
        image_url = self._validate_image_url(image_url, errors=errors)

        if errors:
            raise ValidationError(
                message="Validation failed for listing creation.",
                details={"errors": errors},
            )

        return title, description, price, location, image_url

    def _add_error(self, errors: dict[str, list[str]], field: str, message: str):
        """
        Helper method to add validation errors to the errors dictionary.
        To be able to return multiple error messages at once to the frontend

        Args:
            errors (dict[str, list[str]]): The dictionary to store validation errors.
            field (str): The name of the field that failed validation.
            message (str): The error message describing the validation failure.
        """
        errors.setdefault(field, []).append(message)

    def _validate_title(self, title: str, errors: dict[str, list[str]]) -> str:
        """Validate listing title

        Args:
            title (str): The title to validate.

        Raises:
            ValidationError: If the title is empty or contains only whitespace.

        Returns:
            str: The validated title.
        """
        if not title or not title.strip():
            self._add_error(
                errors, "title", "Title cannot be empty or whitespace only."
            )
            return ""

        return title

    def _validate_description(
        self, description: str, errors: dict[str, list[str]]
    ) -> str:
        """Validate listing description

        Args:
            description (str): The description to validate.

        Raises:
            ValidationError: If the description is empty.

        Returns:
            str: The validated description.
        """
        if not description:
            self._add_error(errors, "description", "Description cannot be empty.")
            return ""

        return description

    def _validate_price(self, price: float, errors: dict[str, list[str]]) -> float:
        """Validates price for a listing

        Args:
            price (float): The price to validate.

        Raises:
            ValidationError: If price is None or negative.
            ValidationError: If price is not a number.

        Returns:
            float: The validated price.
        """
        default_price: float = 0.0
        if price is None:
            self._add_error(errors, "price", "Price cannot be None.")
            return default_price

        if price <= 0:
            self._add_error(errors, "price", "Price must be a non-negative number.")
            return default_price

        return price

    def _validate_location(self, location: str, errors: dict[str, list[str]]) -> str:
        """Validates location for a listing

        Args:
            location (str): The location to validate.

        Raises:
            ValidationError: If the location is empty.

        Returns:
            str: The validated location.
        """
        if not location:
            self._add_error(errors, "location", "Location cannot be empty.")
            return ""
        return location

    def _validate_image_url(
        self, image_url: str | None, errors: dict[str, list[str]]
    ) -> str | None:
        """Validate image URL for a listing

        Args:
            image_url (str | None): The image URL to validate.

        Raises:
            ValidationError: If the image URL is invalid.
            ValidationError: If the image URL does not have a valid domain.

        Returns:
            str | None: image url if valid, otherwise None

        Rules:
        - If image_url is None, return None (indicating no image provided).
        - If image_url is not None, it must be a non-empty string that starts with "http://" or "https://".
        - The URL must have a valid domain network location (e.g., example.com).
        """
        if image_url is None:
            return None

        image_url = image_url.strip()

        if not image_url:
            self._add_error(
                errors, "image_url", "Image URL cannot be empty if provided."
            )
            return None

        parse = urlparse(image_url)

        if parse.scheme not in ("http", "https"):
            self._add_error(
                errors, "image_url", "Image URL must start with http:// or https://"
            )
            return None

        # check if url has a valid domain (e.g., example.com)
        if not parse.netloc:
            self._add_error(errors, "image_url", "Image URL must have a valid domain.")
            return None

        return image_url
