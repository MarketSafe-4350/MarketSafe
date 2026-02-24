"""
NOTE:
Connection-level errors (OperationalError) are handled in DBUtility
and converted into DatabaseUnavailableError.

This class only handles query-level failures.
"""

from __future__ import annotations

from typing import List, Optional
from typing_extensions import override

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.domain_models import Comment
from src.db import DBUtility, CommentMapper
from src.utils import Validation, DatabaseQueryError, CommentNotFoundError
from src.db.comment import CommentDB


class MySQLCommentDB(CommentDB):
    def __init__(self, db: DBUtility) -> None:
        super().__init__(db)

    # -----------------------------
    # CREATE
    # -----------------------------
    @override
    def add(self, comment: Comment) -> Comment:
        Validation.require_not_none(comment, "comment")

        listing_id = Validation.require_int(comment.listing_id, "listing_id")
        author_id = Validation.require_int(comment.author_id, "author_id")
        body = (
            None
            if comment.body is None
            else Validation.require_str(comment.body, "body")
        )

        sql = text(
            """
            INSERT INTO comment (body, listing_id, author_id)
            VALUES (:body, :listing_id, :author_id)
        """
        )

        try:
            with self._db.transaction() as conn:
                result = conn.execute(
                    sql,
                    {
                        "body": body,
                        "listing_id": listing_id,
                        "author_id": author_id,
                    },
                )

                new_id = int(result.lastrowid)

                # If you want created_at included, prefer returning self.get_by_id(new_id)
                return Comment(
                    listing_id=listing_id,
                    author_id=author_id,
                    body=body,
                    comment_id=new_id,
                )

        except IntegrityError as e:
            # FK violation (listing_id/author_id) and other constraints
            raise DatabaseQueryError(
                message="Failed to insert comment (constraint violation).",
                details={"op": "add", "table": "comment"},
            ) from e
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to insert comment.",
                details={"op": "add", "table": "comment"},
            ) from e

    # -----------------------------
    # READ
    # -----------------------------
    @override
    def get_by_id(self, comment_id: int) -> Optional[Comment]:
        comment_id = Validation.require_int(comment_id, "comment_id")

        sql = text(
            """
            SELECT id, created_date, body, listing_id, author_id
            FROM comment
            WHERE id = :id
        """
        )

        try:
            with self._db.connect() as conn:
                row = conn.execute(sql, {"id": comment_id}).mappings().first()
                return None if row is None else CommentMapper.from_mapping(row)
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch comment by id.",
                details={"op": "get_by_id", "table": "comment"},
            ) from e

    @override
    def get_by_listing_id(self, listing_id: int) -> List[Comment]:
        listing_id = Validation.require_int(listing_id, "listing_id")

        # see the newest comments by default
        sql = text(
            """
            SELECT id, created_date, body, listing_id, author_id
            FROM comment
            WHERE listing_id = :listing_id
            ORDER BY created_date ASC, id ASC
        """
        )

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql, {"listing_id": listing_id}).mappings().all()
                return [CommentMapper.from_mapping(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch comments by listing id.",
                details={"op": "get_by_listing_id", "table": "comment"},
            ) from e

    @override
    def get_by_author_id(self, author_id: int) -> List[Comment]:
        author_id = Validation.require_int(author_id, "author_id")

        sql = text(
            """
            SELECT id, created_date, body, listing_id, author_id
            FROM comment
            WHERE author_id = :author_id
            ORDER BY created_date DESC, id DESC
        """
        )

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql, {"author_id": author_id}).mappings().all()
                return [CommentMapper.from_mapping(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch comments by author id.",
                details={"op": "get_by_author_id", "table": "comment"},
            ) from e

    # -----------------------------
    # UPDATE
    # -----------------------------
    @override
    def update_body(self, comment_id: int, body: str | None) -> None:
        comment_id = Validation.require_int(comment_id, "comment_id")
        if body is not None:
            body = Validation.require_str(body, "body")

        sql = text(
            """
            UPDATE comment
            SET body = :body
            WHERE id = :id
        """
        )

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {"id": comment_id, "body": body})
                if int(result.rowcount or 0) == 0:
                    raise CommentNotFoundError(
                        message=f"Comment not found for id: {comment_id}",
                        details={"comment_id": comment_id},
                    )
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to update comment body.",
                details={"op": "update_body", "table": "comment"},
            ) from e

    # -----------------------------
    # DELETE
    # -----------------------------
    @override
    def remove(self, comment_id: int) -> bool:
        comment_id = Validation.require_int(comment_id, "comment_id")

        sql = text(
            """
            DELETE FROM comment
            WHERE id = :id
        """
        )

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {"id": comment_id})
                return (result.rowcount or 0) > 0
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to delete comment.",
                details={"op": "remove", "table": "comment"},
            ) from e
