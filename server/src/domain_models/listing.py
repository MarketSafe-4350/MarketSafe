from __future__ import annotations

from src.utils import ValidationError, UnapprovedBehaviorError, Validation
from typing import List
from src.domain_models.comment import Comment


class Listing:
    """
    Domain Entity: Listing

    Represents the `listing` table in the database.

    Key Invariants / Rules:
    - seller_id is required.
    - title, description, price are required.
    - is_sold indicates whether the listing is sold.
    - sold_to_id must be set when is_sold is True (DB trigger enforces it too).
    - id can only be assigned once (after DB persistence).
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

        self._comments: List[Comment] | None = None
        self.comments = comments  # use setter's Validation

        self._enforce_sold_invariants()

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

    # Intentionally no setter unless you want it for tests then add one.

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
        buyer_account_id = Validation.is_positive_number(buyer_account_id, "sold_to_id")
        if self._is_sold:
            raise UnapprovedBehaviorError("Listing is already sold.")
        self._is_sold = True
        self._sold_to_id = buyer_account_id
        self._enforce_sold_invariants()

    def _enforce_sold_invariants(self) -> None:
        if self._is_sold and self._sold_to_id is None:
            raise ValidationError("sold_to_id must be set when is_sold is True.")
        if (not self._is_sold) and self._sold_to_id is not None:
            raise ValidationError("sold_to_id must be None when is_sold is False.")

    # ==============================
    # comments (NULLABLE)
    # ==============================
    @property
    def comments(self) -> List[Comment] | None:
        return self._comments

    @comments.setter
    def comments(self, value: List[Comment] | None) -> None:
        if value is None:
            self._comments = None
            return

        if not isinstance(value, list):
            raise ValidationError("comments must be a list of Comment.")

        for i, comment in enumerate(value):
            if not isinstance(comment, Comment):
                raise ValidationError(f"comments[{i}] must be a Comment.")

        # shallow copy list for safety measure from external mutation
        self._comments = list(value)

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
            f"created_at={self._created_at!r}"
            f"comments={self._comments})"
        )
