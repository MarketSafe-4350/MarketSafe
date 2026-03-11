# src/db/rating/mysql_rating_db.py
"""
NOTE:
Connection-level errors (OperationalError) are handled in DBUtility
and converted into DatabaseUnavailableError.

This class only handles query-level failures.
"""
from __future__ import annotations

from typing import Optional, List

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing_extensions import override

from src.db import DBUtility
from src.db.rating import RatingDB
from src.db.utils.rating_mapper import RatingMapper
from src.domain_models import Rating
from src.utils import (
    Validation,
    ValidationError,
    DatabaseQueryError,
    RatingNotFoundError,
)


class MySQLRatingDB(RatingDB):
    def __init__(self, db: DBUtility) -> None:
        super().__init__(db)


    # -----------------------------
    # BASE CLASS METHODS
    # -----------------------------
    @override
    def get_average_rating_by_account_id(self, account_id: int) -> float | None:
        """
        Average rating received by a seller across the seller's listings.
        """
        Validation.require_int(account_id, "account_id")

        sql = text("""
            SELECT AVG(r.transaction_rating) AS avg_rating
            FROM rating r
            INNER JOIN listing l ON l.id = r.listing_id
            WHERE l.seller_id = :account_id
        """)

        try:
            with self._db.connect() as conn:
                row = conn.execute(sql, {"account_id": account_id}).mappings().first()
                if row is None or row["avg_rating"] is None:
                    return None
                return float(row["avg_rating"])
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch average rating for account.",
                details={"op": "get_average_rating_by_account_id", "table": "rating"},
            ) from e

    @override
    def get_sum_of_ratings_given_by_account_id(self, account_id: int) -> int:
        """
        Sum of ratings given by a rater/account.
        """
        Validation.require_int(account_id, "account_id")

        sql = text("""
            SELECT COALESCE(SUM(transaction_rating), 0) AS total_rating_sum
            FROM rating
            WHERE rater_id = :account_id
        """)

        try:
            with self._db.connect() as conn:
                row = conn.execute(sql, {"account_id": account_id}).mappings().first()
                return int(row["total_rating_sum"] or 0)
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch sum of ratings given by account.",
                details={"op": "get_sum_of_ratings_given_by_account_id", "table": "rating"},
            ) from e

    @override
    def get_sum_of_ratings_received_by_account_id(self, account_id: int) -> int:
        """
        Sum of ratings received by a seller across all their listings.
        """

        Validation.require_int(account_id, "account_id")

        sql = text("""
            SELECT COALESCE(SUM(r.transaction_rating), 0) AS total_rating_sum
            FROM rating r
            INNER JOIN listing l ON l.id = r.listing_id
            WHERE l.seller_id = :account_id
        """)

        try:
            with self._db.connect() as conn:
                row = conn.execute(sql, {"account_id": account_id}).mappings().first()
                return int(row["total_rating_sum"] or 0)

        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch sum of ratings received by account.",
                details={
                    "op": "get_sum_of_ratings_received_by_account_id",
                    "table": "rating"
                },
            ) from e
    # -----------------------------
    # CREATE
    # -----------------------------
    @override
    def add(self, rating: Rating) -> Rating:
        Validation.require_not_none(rating, "rating")

        sql = text("""
            INSERT INTO rating (transaction_rating, listing_id, rater_id)
            VALUES (:transaction_rating, :listing_id, :rater_id)
        """)

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {
                    "transaction_rating": rating.transaction_rating,
                    "listing_id": rating.listing_id,
                    "rater_id": rating.rater_id,
                })

                new_id = int(result.lastrowid)

                return Rating(
                    listing_id=rating.listing_id,
                    rater_id=rating.rater_id,
                    transaction_rating=rating.transaction_rating,
                    rating_id=new_id,
                )

        except IntegrityError as e:
            raise DatabaseQueryError(
                message="Failed to insert rating due to constraint violation.",
                details={
                    "op": "add",
                    "table": "rating",
                    "listing_id": rating.listing_id,
                    "rater_id": rating.rater_id,
                },
            ) from e
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to insert rating.",
                details={"op": "add", "table": "rating"},
            ) from e

    # -----------------------------
    # READ
    # -----------------------------
    @override
    def get_by_id(self, rating_id: int) -> Optional[Rating]:
        Validation.require_int(rating_id, "rating_id")

        sql = text("""
            SELECT id, created_at, transaction_rating, listing_id, rater_id
            FROM rating
            WHERE id = :id
        """)

        try:
            with self._db.connect() as conn:
                row = conn.execute(sql, {"id": rating_id}).mappings().first()
                return None if row is None else RatingMapper.from_mapping(row)
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch rating by id.",
                details={"op": "get_by_id", "table": "rating"},
            ) from e

    @override
    def get_by_listing_id(self, listing_id: int) -> Optional[Rating]:
        Validation.require_int(listing_id, "listing_id")

        sql = text("""
            SELECT id, created_at, transaction_rating, listing_id, rater_id
            FROM rating
            WHERE listing_id = :listing_id
        """)

        try:
            with self._db.connect() as conn:
                row = conn.execute(sql, {"listing_id": listing_id}).mappings().first()
                return None if row is None else RatingMapper.from_mapping(row)
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch rating by listing id.",
                details={"op": "get_by_listing_id", "table": "rating"},
            ) from e

    @override
    def get_by_rater_id(self, rater_id: int) -> List[Rating]:
        Validation.require_int(rater_id, "rater_id")

        sql = text("""
            SELECT id, created_at, transaction_rating, listing_id, rater_id
            FROM rating
            WHERE rater_id = :rater_id
            ORDER BY created_at DESC, id DESC
        """)

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql, {"rater_id": rater_id}).mappings().all()
                return [RatingMapper.from_mapping(row) for row in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch ratings by rater id.",
                details={"op": "get_by_rater_id", "table": "rating"},
            ) from e

    @override
    def get_all(self) -> List[Rating]:
        sql = text("""
            SELECT id, created_at, transaction_rating, listing_id, rater_id
            FROM rating
            ORDER BY id ASC
        """)

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql).mappings().all()
                return [RatingMapper.from_mapping(row) for row in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch ratings.",
                details={"op": "get_all", "table": "rating"},
            ) from e

    @override
    def get_recent(self, limit: int = 50, offset: int = 0) -> List[Rating]:
        Validation.require_int(limit, "limit")
        Validation.require_int(offset, "offset")

        if limit < 0:
            raise ValidationError("limit must be >= 0.")
        if offset < 0:
            raise ValidationError("offset must be >= 0.")

        sql = text("""
            SELECT id, created_at, transaction_rating, listing_id, rater_id
            FROM rating
            ORDER BY created_at DESC, id DESC
            LIMIT :limit OFFSET :offset
        """)

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql, {
                    "limit": limit,
                    "offset": offset,
                }).mappings().all()
                return [RatingMapper.from_mapping(row) for row in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch recent ratings.",
                details={"op": "get_recent", "table": "rating"},
            ) from e

    @override
    def get_by_score(self, transaction_rating: int) -> List[Rating]:
        Validation.require_int(transaction_rating, "transaction_rating")

        sql = text("""
            SELECT id, created_at, transaction_rating, listing_id, rater_id
            FROM rating
            WHERE transaction_rating = :transaction_rating
            ORDER BY created_at DESC, id DESC
        """)

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql, {
                    "transaction_rating": transaction_rating,
                }).mappings().all()
                return [RatingMapper.from_mapping(row) for row in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch ratings by score.",
                details={"op": "get_by_score", "table": "rating"},
            ) from e

    # -----------------------------
    # AGGREGATE / SUMMARY QUERIES
    # -----------------------------
    @override
    def get_average_for_rater(self, rater_id: int) -> Optional[float]:
        Validation.require_int(rater_id, "rater_id")

        sql = text("""
            SELECT AVG(transaction_rating) AS avg_rating
            FROM rating
            WHERE rater_id = :rater_id
        """)

        try:
            with self._db.connect() as conn:
                row = conn.execute(sql, {"rater_id": rater_id}).mappings().first()
                if row is None or row["avg_rating"] is None:
                    return None
                return float(row["avg_rating"])
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch average rating for rater.",
                details={"op": "get_average_for_rater", "table": "rating"},
            ) from e

    @override
    def count_by_rater(self, rater_id: int) -> int:
        Validation.require_int(rater_id, "rater_id")

        sql = text("""
            SELECT COUNT(*) AS rating_count
            FROM rating
            WHERE rater_id = :rater_id
        """)

        try:
            with self._db.connect() as conn:
                row = conn.execute(sql, {"rater_id": rater_id}).mappings().first()
                return int(row["rating_count"] or 0)
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to count ratings by rater.",
                details={"op": "count_by_rater", "table": "rating"},
            ) from e

    # -----------------------------
    # UPDATE
    # -----------------------------
    @override
    def update(self, rating: Rating) -> Rating:
        Validation.require_not_none(rating, "rating")
        Validation.require_not_none(rating.id, "rating.id")

        sql = text("""
            UPDATE rating
            SET transaction_rating = :transaction_rating,
                listing_id = :listing_id,
                rater_id = :rater_id
            WHERE id = :id
        """)

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {
                    "id": rating.id,
                    "transaction_rating": rating.transaction_rating,
                    "listing_id": rating.listing_id,
                    "rater_id": rating.rater_id,
                })

                if int(result.rowcount or 0) == 0:
                    raise RatingNotFoundError(
                        message=f"Rating not found for id: {rating.id}",
                        details={"rating_id": rating.id},
                    )

            updated = self.get_by_id(rating.id)
            if updated is None:
                raise RatingNotFoundError(
                    message=f"Rating not found after update for id: {rating.id}",
                    details={"rating_id": rating.id},
                )
            return updated

        except RatingNotFoundError:
            raise
        except IntegrityError as e:
            raise DatabaseQueryError(
                message="Failed to update rating due to constraint violation.",
                details={"op": "update", "table": "rating", "rating_id": rating.id},
            ) from e
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to update rating.",
                details={"op": "update", "table": "rating", "rating_id": rating.id},
            ) from e

    @override
    def set_score(self, rating_id: int, transaction_rating: int) -> None:
        Validation.require_int(rating_id, "rating_id")
        Validation.require_int(transaction_rating, "transaction_rating")

        sql = text("""
            UPDATE rating
            SET transaction_rating = :transaction_rating
            WHERE id = :id
        """)

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {
                    "id": rating_id,
                    "transaction_rating": transaction_rating,
                })

                if int(result.rowcount or 0) == 0:
                    raise RatingNotFoundError(
                        message=f"Rating not found for id: {rating_id}",
                        details={"rating_id": rating_id},
                    )

        except RatingNotFoundError:
            raise
        except IntegrityError as e:
            raise DatabaseQueryError(
                message="Failed to update rating score due to constraint violation.",
                details={"op": "set_score", "table": "rating", "rating_id": rating_id},
            ) from e
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to update rating score.",
                details={"op": "set_score", "table": "rating", "rating_id": rating_id},
            ) from e

    # -----------------------------
    # DELETE
    # -----------------------------
    @override
    def remove(self, rating_id: int) -> bool:
        Validation.require_int(rating_id, "rating_id")

        sql = text("""
            DELETE
            FROM rating
            WHERE id = :id
        """)

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {"id": rating_id})
                return (result.rowcount or 0) > 0
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to delete rating.",
                details={"op": "remove", "table": "rating", "rating_id": rating_id},
            ) from e

    @override
    def remove_by_listing_id(self, listing_id: int) -> bool:
        Validation.require_int(listing_id, "listing_id")

        sql = text("""
            DELETE
            FROM rating
            WHERE listing_id = :listing_id
        """)

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {"listing_id": listing_id})
                return (result.rowcount or 0) > 0
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to delete rating by listing id.",
                details={"op": "remove_by_listing_id", "table": "rating", "listing_id": listing_id},
            ) from e
