from __future__ import annotations

from src.utils import ValidationError, UnapprovedBehaviorError, Validation


class Rating:
    """
    Domain Entity: Rating

    Represents the `rating` table in the database.

    Key Invariants / Rules:
    - listing_id is required.
    - rater_id is required.
    - transaction_rating is required.
    - id can only be assigned once (after DB persistence).
    - created_at is DB-managed.
    - Database trigger enforces:
        * listing must be sold
        * only the buyer can rate the listing
    """

    def __init__(
        self,
        listing_id: int,
        rater_id: int,
        transaction_rating: int,
        *,
        rating_id: int | None = None,
        created_at=None,  # DB-managed; keep flexible to avoid coupling
    ):
        self._id = rating_id
        self._listing_id = Validation.require_int(listing_id, "listing_id")
        self._rater_id = Validation.require_int(rater_id, "rater_id")
        self._transaction_rating = self._validate_transaction_rating(transaction_rating)
        self._created_at = created_at

    # ==============================
    # ID (read-only, may be None before DB insert)
    # ==============================

    @property
    def id(self) -> int | None:
        return self._id

    def mark_persisted(self, rating_id: int) -> None:
        if rating_id is None:
            raise ValidationError("Rating ID cannot be None.")
        if self._id is not None:
            raise UnapprovedBehaviorError("Rating ID has already been assigned.")
        self._id = rating_id

    # ==============================
    # LISTING ID (NOT NULL)
    # ==============================

    @property
    def listing_id(self) -> int:
        return self._listing_id

    @listing_id.setter
    def listing_id(self, value: int) -> None:
        self._listing_id = Validation.require_int(value, "listing_id")

    # ==============================
    # RATER ID (NOT NULL)
    # ==============================

    @property
    def rater_id(self) -> int:
        return self._rater_id

    @rater_id.setter
    def rater_id(self, value: int) -> None:
        self._rater_id = Validation.require_int(value, "rater_id")

    # ==============================
    # TRANSACTION RATING (NOT NULL)
    # ==============================

    @property
    def transaction_rating(self) -> int:
        return self._transaction_rating

    @transaction_rating.setter
    def transaction_rating(self, value: int) -> None:
        self._transaction_rating = self._validate_transaction_rating(value)

    def _validate_transaction_rating(self, value: int) -> int:
        value = Validation.require_int(value, "transaction_rating")

        # Adjust this range if your project uses a different scale
        if value < 1 or value > 5:
            raise ValidationError("transaction_rating must be between 1 and 5.")

        return value

    # ==============================
    # CREATED AT (DB-managed)
    # ==============================

    @property
    def created_at(self):
        return self._created_at

    # Intentionally no setter unless needed for tests.

    # ==============================
    # DEBUG REPRESENTATION
    # ==============================

    def __repr__(self) -> str:
        return (
            f"Rating(id={self._id}, "
            f"listing_id={self._listing_id}, "
            f"rater_id={self._rater_id}, "
            f"transaction_rating={self._transaction_rating}, "
            f"created_at={self._created_at!r})"
        )
