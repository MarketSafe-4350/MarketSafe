from __future__ import annotations

from typing import Any, Mapping, Optional, List

from src.domain_models import Listing
from src.domain_models import Comment


class ListingMapper:
    """
    Responsible for converting DB rows/dicts into Listing objects.

    Keep all mapping logic here so the DB implementation stays clean.

    NOTE:
    All SELECT queries must use:
        result.mappings().first()
        result.mappings().all()
    So this class never touches SQLAlchemy internals.
    """

    @staticmethod
    def from_mapping(m: Mapping[str, Any]) -> Listing:
        """
        Accepts a dict-like mapping with keys typically like:
        id, seller_id, title, description, price, image_url, location,
        created_at, is_sold, sold_to_id

        Notes:
        - comments are not mapped here (usually loaded via a separate query).
        """
        return Listing(
            seller_id=int(m["seller_id"]),
            title=str(m["title"]),
            description=str(m["description"]),
            price=float(m["price"]),
            listing_id=int(m["id"]) if m.get("id") is not None else None,
            image_url=(None if m.get("image_url") is None else str(m["image_url"])),
            location=(None if m.get("location") is None else str(m["location"])),
            created_at=m.get("created_at"),
            is_sold=bool(m.get("is_sold", False)),
            sold_to_id=(None if m.get("sold_to_id") is None else int(m["sold_to_id"])),
            comments=None,  # loaded separately (join or another query)
        )

    @staticmethod
    def from_mapping_with_comments(
        m: Mapping[str, Any],
        comments: Optional[List[Comment]],
    ) -> Listing:
        """
        Convenience helper if your DB layer loads listing + comments separately.
        """
        listing = ListingMapper.from_mapping(m)
        listing.comments = comments  # runs your validation + shallow copy
        return listing
