"""
NOTE:
Connection-level errors (OperationalError) are handled in DBUtility
and converted into DatabaseUnavailableError.

This class only handles query-level failures.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing_extensions import override

from src.db import DBUtility, OfferMapper
from src.db.offer import OfferDB
from src.domain_models import Offer
from src.utils import Validation, DatabaseQueryError, OfferNotFoundError


class MySQLOfferDB(OfferDB):
    def __init__(self, db: DBUtility) -> None:
        super().__init__(db)

    # -----------------------------
    # CREATE
    # -----------------------------
    @override
    def add(self, offer: Offer) -> Offer:
        Validation.require_not_none(offer, "offer")

        listing_id = Validation.require_int(offer.listing_id, "listing_id")
        sender_id = Validation.require_int(offer.sender_id, "sender_id")
        offered_price = Validation.is_positive_number(
            offer.offered_price, "offered_price"
        )

        sql = text(
            """
            INSERT INTO offer
                (listing_id, sender_id, offered_price, location_offered, seen, accepted)
            VALUES
                (:listing_id, :sender_id, :offered_price, :location_offered, :seen, :accepted)
        """
        )

        try:
            with self._db.transaction() as conn:
                result = conn.execute(
                    sql,
                    {
                        "listing_id": listing_id,
                        "sender_id": sender_id,
                        "offered_price": float(offered_price),
                        "location_offered": offer.location_offered,
                        "seen": bool(offer.seen),
                        "accepted": offer.accepted,
                    },
                )

                new_id = int(result.lastrowid)
                offer.mark_persisted(new_id)
                return offer

        except IntegrityError as e:
            raise DatabaseQueryError(
                message="Failed to insert offer (constraint violation).",
                details={"op": "add", "table": "offer"},
            ) from e
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to insert offer.",
                details={"op": "add", "table": "offer"},
            ) from e

    # -----------------------------
    # READ
    # -----------------------------
    @override
    def get_by_id(self, offer_id: int) -> Optional[Offer]:
        offer_id = Validation.require_int(offer_id, "offer_id")

        sql = text(
            """
            SELECT id, listing_id, sender_id, offered_price, location_offered,
                   created_date, seen, accepted
            FROM offer
            WHERE id = :id
        """
        )

        try:
            with self._db.connect() as conn:
                row = conn.execute(sql, {"id": offer_id}).mappings().first()
                return None if row is None else OfferMapper.from_mapping(row)
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch offer by id.",
                details={"op": "get_by_id", "table": "offer"},
            ) from e

    @override
    def get_all(self) -> List[Offer]:
        sql = text(
            """
            SELECT id, listing_id, sender_id, offered_price, location_offered,
                   created_date, seen, accepted
            FROM offer
            ORDER BY created_date DESC, id DESC
        """
        )

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql).mappings().all()
                return [OfferMapper.from_mapping(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch all offers.",
                details={"op": "get_all", "table": "offer"},
            ) from e

    @override
    def get_by_listing_id(self, listing_id: int) -> List[Offer]:
        listing_id = Validation.require_int(listing_id, "listing_id")

        sql = text(
            """
            SELECT id, listing_id, sender_id, offered_price, location_offered,
                   created_date, seen, accepted
            FROM offer
            WHERE listing_id = :listing_id
            ORDER BY created_date DESC, id DESC
        """
        )

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql, {"listing_id": listing_id}).mappings().all()
                return [OfferMapper.from_mapping(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch offers by listing.",
                details={"op": "get_by_listing_id", "table": "offer"},
            ) from e

    @override
    def get_by_sender_id(self, sender_id: int) -> List[Offer]:
        sender_id = Validation.require_int(sender_id, "sender_id")

        sql = text(
            """
            SELECT id, listing_id, sender_id, offered_price, location_offered,
                   created_date, seen, accepted
            FROM offer
            WHERE sender_id = :sender_id
            ORDER BY created_date DESC, id DESC
        """
        )

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql, {"sender_id": sender_id}).mappings().all()
                return [OfferMapper.from_mapping(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch offers by sender.",
                details={"op": "get_by_sender_id", "table": "offer"},
            ) from e

    @override
    def get_accepted_by_listing_id(self, listing_id: int) -> List[Offer]:
        listing_id = Validation.require_int(listing_id, "listing_id")

        sql = text(
            """
            SELECT id, listing_id, sender_id, offered_price, location_offered,
                   created_date, seen, accepted
            FROM offer
            WHERE listing_id = :listing_id
              AND accepted = TRUE
            ORDER BY created_date DESC, id DESC
        """
        )

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql, {"listing_id": listing_id}).mappings().all()
                return [OfferMapper.from_mapping(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch accepted offers by listing.",
                details={"op": "get_accepted_by_listing_id", "table": "offer"},
            ) from e

    @override
    def get_unseen_by_listing_id(self, listing_id: int) -> List[Offer]:
        listing_id = Validation.require_int(listing_id, "listing_id")

        sql = text(
            """
            SELECT id, listing_id, sender_id, offered_price, location_offered,
                   created_date, seen, accepted
            FROM offer
            WHERE listing_id = :listing_id
              AND seen = FALSE
            ORDER BY created_date DESC, id DESC
        """
        )

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql, {"listing_id": listing_id}).mappings().all()
                return [OfferMapper.from_mapping(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch unseen offers by listing.",
                details={"op": "get_unseen_by_listing_id", "table": "offer"},
            ) from e

    @override
    def get_pending_by_listing_id(self, listing_id: int) -> List[Offer]:
        listing_id = Validation.require_int(listing_id, "listing_id")

        sql = text(
            """
            SELECT id, listing_id, sender_id, offered_price, location_offered,
                   created_date, seen, accepted
            FROM offer
            WHERE listing_id = :listing_id
              AND accepted IS NULL
            ORDER BY created_date DESC, id DESC
        """
        )

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql, {"listing_id": listing_id}).mappings().all()
                return [OfferMapper.from_mapping(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch pending offers by listing.",
                details={"op": "get_pending_by_listing_id", "table": "offer"},
            ) from e

    @override
    def get_by_sender_and_listing(
        self, sender_id: int, listing_id: int
    ) -> Optional[Offer]:
        sender_id = Validation.require_int(sender_id, "sender_id")
        listing_id = Validation.require_int(listing_id, "listing_id")

        sql = text(
            """
            SELECT id, listing_id, sender_id, offered_price, location_offered,
                   created_date, seen, accepted
            FROM offer
            WHERE sender_id = :sender_id
              AND listing_id = :listing_id
        """
        )

        try:
            with self._db.connect() as conn:
                row = (
                    conn.execute(
                        sql, {"sender_id": sender_id, "listing_id": listing_id}
                    )
                    .mappings()
                    .first()
                )
                return None if row is None else OfferMapper.from_mapping(row)
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch offer by sender and listing.",
                details={"op": "get_by_sender_and_listing", "table": "offer"},
            ) from e

    # -----------------------------
    # UPDATE
    # -----------------------------
    @override
    def set_seen(self, offer_id: int) -> None:
        offer_id = Validation.require_int(offer_id, "offer_id")

        sql = text(
            """
            UPDATE offer
            SET seen = TRUE
            WHERE id = :id
        """
        )

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {"id": offer_id})
                if int(result.rowcount or 0) == 0:
                    raise OfferNotFoundError(
                        message=f"Offer not found for id: {offer_id}",
                        details={"offer_id": offer_id},
                    )
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to mark offer as seen.",
                details={"op": "set_seen", "table": "offer"},
            ) from e

    @override
    def set_accepted(self, offer_id: int, accepted: bool) -> None:
        offer_id = Validation.require_int(offer_id, "offer_id")
        accepted = Validation.is_boolean(accepted, "accepted")

        sql = text(
            """
            UPDATE offer
            SET accepted = :accepted
            WHERE id = :id
        """
        )

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {"id": offer_id, "accepted": bool(accepted)})
                if int(result.rowcount or 0) == 0:
                    raise OfferNotFoundError(
                        message=f"Offer not found for id: {offer_id}",
                        details={"offer_id": offer_id},
                    )
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to update offer accepted state.",
                details={"op": "set_accepted", "table": "offer"},
            ) from e

    # -----------------------------
    # DELETE
    # -----------------------------
    @override
    def remove(self, offer_id: int) -> bool:
        offer_id = Validation.require_int(offer_id, "offer_id")

        sql = text(
            """
            DELETE FROM offer
            WHERE id = :id
        """
        )

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {"id": offer_id})
                return (result.rowcount or 0) > 0
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to delete offer.",
                details={"op": "remove", "table": "offer"},
            ) from e
