from src.domain_models.listing import Listing
from src.utils.errors import (
    ValidationError,
    DatabaseUnavailableError,
    DatabaseQueryError,
)
from src.utils import ListingNotFoundError, UnapprovedBehaviorError
from urllib.parse import urlparse
from typing import List
from src.business_logic.managers.listing import IListingManager


class ListingService:
    """Service class for handling listing-related business logic."""

    def __init__(self, listing_manager: IListingManager):
        self._listing_manager = listing_manager

    def get_all_listing(self) -> List[Listing]:
        """Get all listing

        Returns:
            List[Listing]: list of Listing
        """
        return self._listing_manager.list_listings()

    def get_listing_by_user_id(self, user_id) -> List[Listing]:
        """Get current user listing

        Returns:
            List[Listing]: list of Listing
        """
        return self._listing_manager.list_listings_by_seller(user_id)

    def get_listing_by_id(self, listing_id: int) -> Listing | None:
        return self._listing_manager.get_listing_by_id(listing_id)

    def search_listings(self, query: str) -> List[Listing]:
        """Search listings by keywords across title, description, and location.

        Results are ranked by simple relevance, prioritizing title matches.
        """
        if query is None:
            return []

        normalized_query = query.strip().lower()
        if not normalized_query:
            return []

        keywords = [token for token in normalized_query.split() if token]
        if not keywords:
            return []

        listings = self._listing_manager.list_listings()
        scored_results: list[tuple[int, Listing]] = []

        for listing in listings:
            title = (listing.title or "").lower()
            description = (listing.description or "").lower()
            location = (listing.location or "").lower()
            searchable_text = f"{title} {description} {location}"

            # Weighted scoring: title matches count more than description/location.
            score = 0
            for keyword in keywords:
                if keyword in title:
                    score += 3
                elif keyword in searchable_text:
                    score += 1

            if score > 0:
                scored_results.append((score, listing))

        scored_results.sort(
            key=lambda item: (
                -item[0],
                -(item[1].created_at.timestamp() if item[1].created_at else 0),
                -(item[1].id or 0),
            )
        )

        return [listing for _, listing in scored_results]

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

        return self._listing_manager.create_listing(listing)

    def delete_listing(self, listing_id: int, actor_user_id: int) -> bool:
        listing = self._listing_manager.get_listing_by_id(listing_id)
        if listing is None:
            raise ListingNotFoundError(
                message=f"Listing not found for id: {listing_id}",
                details={"listing_id": listing_id},
            )

        if listing.seller_id != actor_user_id:
            raise UnapprovedBehaviorError(
                message="Only the seller can delete this listing.",
                details={
                    "listing_id": listing_id,
                    "seller_id": listing.seller_id,
                    "actor_id": actor_user_id,
                },
            )

        return self._listing_manager.delete_listing(listing_id)

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

        # Allow locally-served uploaded images (e.g. /uploads/listings/<file>)
        if image_url.startswith("/"):
            return image_url

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
