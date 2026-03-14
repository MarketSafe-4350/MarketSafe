from __future__ import annotations

from src.utils import ValidationError, UnapprovedBehaviorError, Validation


class Offer:
    """
    Domain Entity: Offer

    Represents the `offer` table in the database.

    Key Invariants / Rules:
    - listing_id is required.
    - sender_id is required.
    - offered_price is required and must be positive.
    - location_offered is optional (nullable).
    - seen defaults to False; can only transition False -> True.
    - accepted is tri-state:
        None  = pending (default)
        True  = accepted
        False = rejected
      Once accepted or rejected the state cannot change.
    - created_date is DB-managed.
    - id can only be assigned once (after DB persistence).
    """

    def __init__(
        self,
        listing_id: int,
        sender_id: int,
        offered_price: float,
        *,
        offer_id: int | None = None,
        location_offered: str | None = None,
        created_date=None,  # DB-managed; keep flexible to avoid coupling
        seen: bool = False,
        accepted: bool | None = None,
    ):
        self._id = offer_id
        self._listing_id = Validation.require_int(listing_id, "listing_id")
        self._sender_id = Validation.require_int(sender_id, "sender_id")
        self._offered_price = Validation.is_positive_number(offered_price, "offered_price")
        self._location_offered = (
            None
            if location_offered is None
            else Validation.require_str(location_offered, "location_offered")
        )
        self._created_date = created_date
        self._seen = Validation.is_boolean(seen, "seen")
        self._accepted = self._validate_accepted(accepted)

    # ==============================
    # ID (read-only, may be None before DB insert)
    # ==============================

    @property
    def id(self) -> int | None:
        return self._id

    def mark_persisted(self, offer_id: int) -> None:
        if offer_id is None:
            raise ValidationError("Offer ID cannot be None.")
        if self._id is not None:
            raise UnapprovedBehaviorError("Offer ID has already been assigned.")
        self._id = offer_id

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
    # SENDER ID (NOT NULL)
    # ==============================

    @property
    def sender_id(self) -> int:
        return self._sender_id

    @sender_id.setter
    def sender_id(self, value: int) -> None:
        self._sender_id = Validation.require_int(value, "sender_id")

    # ==============================
    # OFFERED PRICE (NOT NULL, positive)
    # ==============================

    @property
    def offered_price(self) -> float:
        return self._offered_price

    @offered_price.setter
    def offered_price(self, value: float) -> None:
        self._offered_price = Validation.is_positive_number(value, "offered_price")

    # ==============================
    # LOCATION OFFERED (NULLABLE)
    # ==============================

    @property
    def location_offered(self) -> str | None:
        return self._location_offered

    @location_offered.setter
    def location_offered(self, value: str | None) -> None:
        self._location_offered = (
            None
            if value is None
            else Validation.require_str(value, "location_offered")
        )

    # ==============================
    # CREATED DATE (DB-managed)
    # ==============================

    @property
    def created_date(self):
        return self._created_date

    # ==============================
    # SEEN (NOT NULL, default False)
    # ==============================

    @property
    def seen(self) -> bool:
        return self._seen

    def mark_seen(self) -> None:
        self._seen = True

    # ==============================
    # ACCEPTED (tri-state: None=pending, True=accepted, False=rejected)
    # ==============================

    @property
    def accepted(self) -> bool | None:
        return self._accepted

    @property
    def is_pending(self) -> bool:
        return self._accepted is None

    def accept(self) -> None:
        if not self.is_pending:
            raise UnapprovedBehaviorError("Offer has already been resolved.")
        self._accepted = True

    def reject(self) -> None:
        if not self.is_pending:
            raise UnapprovedBehaviorError("Offer has already been resolved.")
        self._accepted = False

    def _validate_accepted(self, value) -> bool | None:
        if value is not None and not isinstance(value, bool):
            raise ValidationError("accepted must be True, False, or None.")
        return value

    # ==============================
    # DEBUG REPRESENTATION
    # ==============================

    def __repr__(self) -> str:
        return (
            f"Offer(id={self._id}, "
            f"listing_id={self._listing_id}, "
            f"sender_id={self._sender_id}, "
            f"offered_price={self._offered_price}, "
            f"location_offered={self._location_offered!r}, "
            f"seen={self._seen}, "
            f"accepted={self._accepted}, "
            f"created_date={self._created_date!r})"
        )
