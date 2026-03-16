from __future__ import annotations

from typing import Any, Mapping

from src.domain_models import Offer


class OfferMapper:
    """
    Responsible for converting DB rows/dicts into Offer objects.

    Keep all mapping logic here so the DB implementation stays clean.

    NOTE:
    All SELECT queries must use:
        result.mappings().first()
        result.mappings().all()
    So this class never touches SQLAlchemy internals.
    """

    @staticmethod
    def from_mapping(m: Mapping[str, Any]) -> Offer:
        """
        Accepts a dict-like mapping with keys:
        id, listing_id, sender_id, offered_price, location_offered,
        created_date, seen, accepted
        """
        return Offer(
            offer_id=int(m["id"]) if m.get("id") is not None else None,
            listing_id=int(m["listing_id"]),
            sender_id=int(m["sender_id"]),
            offered_price=float(m["offered_price"]),
            location_offered=(None if m.get("location_offered") is None else str(m["location_offered"])),
            created_date=m.get("created_date"),
            seen=bool(m.get("seen", False)),
            accepted=(None if m.get("accepted") is None else bool(m["accepted"])),
        )
