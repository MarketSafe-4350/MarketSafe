from __future__ import annotations

from src.domain_models.offer import Offer
from src.utils import ValidationError, UnapprovedBehaviorError, Validation
from typing import List
from src.domain_models.comment import Comment
from src.domain_models.rating import Rating


class Listing:
    """
    Domain Entity: Listing

    Represents the `listing` table in the database.

    Key Invariants / Rules:
    - seller_id is required.
    - title, description, price are required.
    - is_sold indicates whether the listing is sold.
    - sold_to_id must be set when is_sold is True (DB trigger enforces it too).
    - rating can only exist when the listing is sold.
    - id can only be assigned once (after DB persistence).
    - offers is the list of Offer objects associated with this listing.
    """

    def __init__(
        self,
        seller_id: int,
        title: str,
        description: str,
        price: float,
        *,
        listing_id: int | None = None,
        image_url: str | None = None,
        location: str | None = None,
        created_at=None,  # Set by DB; keep flexible type to avoid coupling
        is_sold: bool = False,
        sold_to_id: int | None = None,
        comments: List[Comment] | None = None,
        rating: Rating | None = None,
        offers: List[Offer] | None = None,
    ):
        self._id = listing_id
        self._seller_id = Validation.require_int(seller_id, "seller_id")

        self._title = Validation.require_str(title, "title")
        self._description = Validation.require_str(description, "description")

        self._price = Validation.is_positive_number(price, "price")

        self._image_url = (
            None
            if image_url is None
            else Validation.require_str(image_url, "image_url")
        )
        self._location = (
            None if location is None else Validation.require_str(location, "location")
        )

        self._created_at = created_at
        self._is_sold = Validation.is_boolean(is_sold, "is_sold")
        self._sold_to_id = sold_to_id

        self._comments = list(comments) if comments is not None else []
        self._rating = None if rating is None else rating
        self._offers = list(offers) if offers is not None else []

        self._enforce_sold_invariants()
        self._enforce_rating_invariants()

    # ==============================
    # ID (read-only, may be None before DB insert)
    # ==============================

    @property
    def id(self) -> int | None:
        return self._id

    def mark_persisted(self, listing_id: int) -> None:
        if listing_id is None:
            raise ValidationError("Listing ID cannot be None.")
        if self._id is not None:
            raise UnapprovedBehaviorError("Listing ID has already been assigned.")
        self._id = listing_id

        # Re-check once listing gets a persistent id
        self._enforce_rating_invariants()

    # ==============================
    # SELLER ID (NOT NULL)
    # ==============================

    @property
    def seller_id(self) -> int:
        return self._seller_id

    @seller_id.setter
    def seller_id(self, value: int) -> None:
        self._seller_id = Validation.require_int(value, "seller_id")

    # ==============================
    # TITLE (NOT NULL)
    # ==============================

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self._title = Validation.require_str(value, "title")

    # ==============================
    # DESCRIPTION (NOT NULL)
    # ==============================

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._description = Validation.require_str(value, "description")

    # ==============================
    # IMAGE URL (NULLABLE)
    # ==============================

    @property
    def image_url(self) -> str | None:
        return self._image_url

    @image_url.setter
    def image_url(self, value: str | None) -> None:
        self._image_url = (
            None if value is None else Validation.require_str(value, "image_url")
        )

    # ==============================
    # PRICE (NOT NULL)
    # ==============================

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        self._price = Validation.is_positive_number(value, "price")

    # ==============================
    # LOCATION (NULLABLE)
    # ==============================

    @property
    def location(self) -> str | None:
        return self._location

    @location.setter
    def location(self, value: str | None) -> None:
        self._location = (
            None if value is None else Validation.require_str(value, "location")
        )

    # ==============================
    # CREATED AT (DB-managed)
    # ==============================

    @property
    def created_at(self):
        return self._created_at

    # ==============================
    # SOLD STATE + BUYER
    # ==============================

    @property
    def is_sold(self) -> bool:
        return self._is_sold

    @property
    def sold_to_id(self) -> int | None:
        return self._sold_to_id

    def mark_sold(self, buyer_account_id: int) -> None:
        buyer_account_id = Validation.require_positive_int(
            buyer_account_id, "sold_to_id"
        )
        if self._is_sold:
            raise UnapprovedBehaviorError("Listing is already sold.")
        self._is_sold = True
        self._sold_to_id = buyer_account_id
        self._enforce_sold_invariants()
        self._enforce_rating_invariants()

    def _enforce_sold_invariants(self) -> None:
        if self._is_sold and self._sold_to_id is None:
            raise ValidationError("sold_to_id must be set when is_sold is True.")
        if (not self._is_sold) and self._sold_to_id is not None:
            raise ValidationError("sold_to_id must be None when is_sold is False.")

    # ==============================
    # RATING (NULLABLE, sold listings only)
    # ==============================

    @property
    def rating(self) -> Rating | None:
        return self._rating

    @rating.setter
    def rating(self, value: Rating | None) -> None:
        self._rating = None if value is None else value
        self._enforce_rating_invariants()

    def add_rating(self, rating: Rating) -> None:
        Validation.require_not_none(rating, "rating")

        if self._rating is not None:
            raise UnapprovedBehaviorError("Listing already has a rating.")

        self._rating = rating
        self._enforce_rating_invariants()

    def remove_rating(self) -> None:
        self._rating = None

    def _enforce_rating_invariants(self) -> None:
        if self._rating is None:
            return

        if not self._is_sold:
            raise ValidationError("rating can only be set for a sold listing.")

        if self._id is not None and self._rating.listing_id != self._id:
            raise ValidationError(
                f"rating.listing_id ({self._rating.listing_id}) "
                f"does not match Listing.id ({self._id})."
            )

    # ==============================
    # COMMENTS
    # ==============================

    @property
    def comments(self) -> List[Comment]:
        return list(self._comments)

    @comments.setter
    def comments(self, value: List[Comment] | None) -> None:
        if value is None:
            self._comments = []
            return

        if not isinstance(value, list):
            raise ValidationError("comments must be a list of Comment.")

        for i, comment in enumerate(value):
            if not isinstance(comment, Comment):
                raise ValidationError(f"comments[{i}] must be a Comment.")

        self._comments = list(value)

    def add_comment(self, comment: Comment) -> None:
        Validation.require_not_none(comment, "Comment")

        self._comments.append(comment)

    def add_comments(self, comments: List[Comment]) -> None:
        Validation.require_not_none(comments, "comments")

        if not isinstance(comments, list):
            raise ValidationError("comments must be a list of Comment.")

        for i, comment in enumerate(comments):
            if not isinstance(comment, Comment):
                raise ValidationError(f"comments[{i}] must be a Comment.")

            if self._id is not None and comment.listing_id != self._id:
                raise ValidationError(
                    f"comments[{i}].listing_id ({comment.listing_id}) "
                    f"does not match Listing.id ({self._id})."
                )

            self._comments.append(comment)

    # ==============================
    # OFFERS
    # ==============================

    @property
    def offers(self) -> List[Offer]:
        return list(self._offers)

    @offers.setter
    def offers(self, value: List[Offer] | None) -> None:
        if value is None:
            self._offers = []
            return

        if not isinstance(value, list):
            raise ValidationError("offers must be a list of Offer.")

        for i, offer in enumerate(value):
            if not isinstance(offer, Offer):
                raise ValidationError(f"offers[{i}] must be an Offer.")

        self._offers = list(value)

    def add_offer(self, offer: Offer) -> None:
        Validation.require_not_none(offer, "offer")

        if not isinstance(offer, Offer):
            raise ValidationError("offer must be an Offer.")

        if self._id is not None and offer.listing_id != self._id:
            raise ValidationError(
                f"offer.listing_id ({offer.listing_id}) "
                f"does not match Listing.id ({self._id})."
            )

        self._offers.append(offer)

    # ==============================
    # DEBUG REPRESENTATION
    # ==============================

    def __repr__(self) -> str:
        return (
            f"Listing(id={self._id}, "
            f"seller_id={self._seller_id}, "
            f"title={self._title!r}, "
            f"price={self._price}, "
            f"is_sold={self._is_sold}, "
            f"sold_to_id={self._sold_to_id}, "
            f"created_at={self._created_at!r}, "
            f"rating={self._rating}, "
            f"comments={self._comments}, "
            f"offers={self._offers})"
        )
