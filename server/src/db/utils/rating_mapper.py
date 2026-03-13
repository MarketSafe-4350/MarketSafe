from __future__ import annotations

from typing import Any, Mapping

from src.domain_models import Rating


class RatingMapper:
    """
    Responsible for converting DB rows/dicts into Rating objects.

    Keep all mapping logic here so the DB implementation stays clean.

    NOTE:
    All SELECT queries must use:
        result.mappings().first()
        result.mappings().all()

    So this class never touches SQLAlchemy internals.
    """

    @staticmethod
    def from_mapping(m: Mapping[str, Any]) -> Rating:
        """
        Accepts a dict-like mapping with keys:
        id, created_at, transaction_rating, listing_id, rater_id
        """

        return Rating(
            rating_id=int(m["id"]),
            listing_id=int(m["listing_id"]),
            rater_id=int(m["rater_id"]),
            transaction_rating=int(m["transaction_rating"]),
            created_at=m["created_at"],
        )
