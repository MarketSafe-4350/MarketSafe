from __future__ import annotations

from src.utils import ValidationError, UnapprovedBehaviorError, Validation


class Comment:
    """
    Domain Entity: Comment

    Represents the `comment` table in the database.

    Key Invariants / Rules:
    - listing_id is required.
    - author_id is required.
    - body is nullable in the DB (can be None).
    - created_date is DB-managed (DEFAULT CURRENT_TIMESTAMP).
    - id can only be assigned once (after DB persistence).
    """

    def __init__(
        self,
        listing_id: int,
        author_id: int,
        *,
        body: str | None = None,
        comment_id: int | None = None,
        created_date=None,  # Set by DB; keep flexible type to avoid coupling
    ):
        self._id = comment_id

        self._listing_id = Validation.require_int(listing_id, "listing_id")
        self._author_id = Validation.require_int(author_id, "author_id")

        self._body = None if body is None else Validation.require_str(body, "body")
        self._created_date = created_date

    # ==============================
    # ID (read-only, may be None before DB insert)
    # ==============================

    @property
    def id(self) -> int | None:
        return self._id

    def mark_persisted(self, comment_id: int) -> None:
        if comment_id is None:
            raise ValidationError("Comment ID cannot be None.")
        if self._id is not None:
            raise UnapprovedBehaviorError("Comment ID has already been assigned.")
        self._id = comment_id

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
    # AUTHOR ID (NOT NULL)
    # ==============================

    @property
    def author_id(self) -> int:
        return self._author_id

    @author_id.setter
    def author_id(self, value: int) -> None:
        self._author_id = Validation.require_int(value, "author_id")

    # ==============================
    # BODY (NULLABLE)
    # ==============================

    @property
    def body(self) -> str | None:
        return self._body

    @body.setter
    def body(self, value: str | None) -> None:
        self._body = None if value is None else Validation.require_str(value, "body")

    # ==============================
    # CREATED DATE (DB-managed)
    # ==============================

    @property
    def created_date(self):
        return self._created_date

    # Intentionally no setter unless you want it for tests then add one.

    # ==============================
    # DEBUG REPRESENTATION
    # ==============================

    def __repr__(self) -> str:
        return (
            f"Comment(id={self._id}, "
            f"listing_id={self._listing_id}, "
            f"author_id={self._author_id}, "
            f"body={self._body!r}, "
            f"created_date={self._created_date!r})"
        )
