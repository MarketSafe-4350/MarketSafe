from __future__ import annotations
from typing import Any, Mapping, Optional, List
from src.domain_models.comment import Comment


class CommentMapper:
    """
    Responsible for converting DB rows/dicts into Comment objects.

    Keep all mapping logic here so the DB implementation stays clean.

    NOTE:
    All SELECT queries must use:
        result.mappings().first()
        result.mappings().all()
    So this class never touches SQLAlchemy internals.
    """

    @staticmethod
    def from_mapping(m: Mapping[str, Any]) -> Comment:
        """
        Accepts a dict-like mapping with keys typically like:
        id, created_date, body, listing_id, author_id
        """
        return Comment(
            listing_id=int(m["listing_id"]),
            author_id=int(m["author_id"]),
            body=(None if m.get("body") is None else str(m["body"])),
            comment_id=int(m["id"]) if m.get("id") is not None else None,
            created_date=m.get("created_date"),
        )
