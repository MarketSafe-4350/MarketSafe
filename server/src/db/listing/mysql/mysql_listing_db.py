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

from src.db import DBUtility, ListingMapper
from src.db.listing import ListingDB
from src.domain_models import Listing
from src.utils import Validation, DatabaseQueryError, ListingNotFoundError


class MySQLListingDB(ListingDB):
    def __init__(self, db: DBUtility) -> None:
        super().__init__(db)

    # -----------------------------
    # CREATE
    # -----------------------------
    @override
    def add(self, listing: Listing) -> Listing:
        Validation.require_not_none(listing, "listing")

        seller_id = Validation.require_int(listing.seller_id, "seller_id")
        title = Validation.require_str(listing.title, "title")
        description = Validation.require_str(listing.description, "description")
        price = Validation.is_positive_number(listing.price, "price")

        sql = text("""
            INSERT INTO listing
                (seller_id, title, description, image_url, price, location, is_sold, sold_to_id)
            VALUES
                (:seller_id, :title, :description, :image_url, :price, :location, :is_sold, :sold_to_id)
        """)

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {
                    "seller_id": seller_id,
                    "title": title,
                    "description": description,
                    "image_url": (listing.image_url.strip() if listing.image_url else None),
                    "price": float(price),
                    "location": (listing.location.strip() if listing.location else None),
                    "is_sold": bool(listing.is_sold),
                    "sold_to_id": listing.sold_to_id,
                })

                new_id = int(result.lastrowid)

                # If you want created_at included, prefer returning self.get_by_id(new_id)
                return Listing(
                    seller_id=seller_id,
                    title=title,
                    description=description,
                    price=float(price),
                    listing_id=new_id,
                    image_url=(listing.image_url.strip() if listing.image_url else None),
                    location=(listing.location.strip() if listing.location else None),
                    is_sold=bool(listing.is_sold),
                    sold_to_id=listing.sold_to_id,
                )

        except IntegrityError as e:
            raise DatabaseQueryError(
                message="Failed to insert listing (constraint violation).",
                details={"op": "add", "table": "listing"},
            ) from e
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to insert listing.",
                details={"op": "add", "table": "listing"},
            ) from e

    # -----------------------------
    # READ
    # -----------------------------
    @override
    def get_by_id(self, listing_id: int) -> Optional[Listing]:
        listing_id = Validation.require_int(listing_id, "listing_id")

        sql = text("""
            SELECT id, seller_id, title, description, image_url, price, location,
                   created_at, is_sold, sold_to_id
            FROM listing
            WHERE id = :id
        """)

        try:
            with self._db.connect() as conn:
                row = conn.execute(sql, {"id": listing_id}).mappings().first()
                return None if row is None else ListingMapper.from_mapping(row)
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch listing by id.",
                details={"op": "get_by_id", "table": "listing"},
            ) from e

    @override
    def get_all(self) -> List[Listing]:
        sql = text("""
            SELECT id, seller_id, title, description, image_url, price, location,
                   created_at, is_sold, sold_to_id
            FROM listing
            ORDER BY created_at DESC, id DESC
        """)

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql).mappings().all()
                return [ListingMapper.from_mapping(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch listings.",
                details={"op": "get_all", "table": "listing"},
            ) from e

    @override
    def get_by_seller_id(self, seller_id: int) -> List[Listing]:
        seller_id = Validation.require_int(seller_id, "seller_id")

        sql = text("""
            SELECT id, seller_id, title, description, image_url, price, location,
                   created_at, is_sold, sold_to_id
            FROM listing
            WHERE seller_id = :seller_id
            ORDER BY created_at DESC, id DESC
        """)

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql, {"seller_id": seller_id}).mappings().all()
                return [ListingMapper.from_mapping(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch listings by seller.",
                details={"op": "get_by_seller_id", "table": "listing"},
            ) from e

    @override
    def get_by_buyer_id(self, buyer_id: int) -> List[Listing]:
        buyer_id = Validation.require_int(buyer_id, "buyer_id")

        sql = text("""
            SELECT id, seller_id, title, description, image_url, price, location,
                   created_at, is_sold, sold_to_id
            FROM listing
            WHERE sold_to_id = :buyer_id
            ORDER BY created_at DESC, id DESC
        """)

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql, {"buyer_id": buyer_id}).mappings().all()
                return [ListingMapper.from_mapping(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch listings by buyer.",
                details={"op": "get_by_buyer_id", "table": "listing"},
            ) from e

    @override
    def get_unsold(self) -> List[Listing]:
        sql = text("""
            SELECT id, seller_id, title, description, image_url, price, location,
                   created_at, is_sold, sold_to_id
            FROM listing
            WHERE is_sold = FALSE
            ORDER BY created_at DESC, id DESC
        """)

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql).mappings().all()
                return [ListingMapper.from_mapping(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch unsold listings.",
                details={"op": "get_unsold", "table": "listing"},
            ) from e

    # -----------------------------
    # SAFER, PARAMETERIZED QUERIES
    # -----------------------------
    @override
    def get_unsold_by_location(self, location: str) -> List[Listing]:
        location = Validation.require_str(location, "location")

        sql = text("""
            SELECT id, seller_id, title, description, image_url, price, location,
                   created_at, is_sold, sold_to_id
            FROM listing
            WHERE is_sold = FALSE
              AND location LIKE :loc
            ORDER BY created_at DESC, id DESC
        """)

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql, {"loc": f"%{location}%"}).mappings().all()
                return [ListingMapper.from_mapping(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch unsold listings by location.",
                details={"op": "get_unsold_by_location", "table": "listing"},
            ) from e

    @override
    def get_unsold_by_max_price(self, max_price: float) -> List[Listing]:
        max_price = Validation.is_positive_number(max_price, "max_price")

        sql = text("""
            SELECT id, seller_id, title, description, image_url, price, location,
                   created_at, is_sold, sold_to_id
            FROM listing
            WHERE is_sold = FALSE
              AND price <= :max_price
            ORDER BY created_at DESC, id DESC
        """)

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql, {"max_price": float(max_price)}).mappings().all()
                return [ListingMapper.from_mapping(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch unsold listings by max price.",
                details={"op": "get_unsold_by_max_price", "table": "listing"},
            ) from e

    @override
    def get_unsold_by_location_and_max_price(self, location: str, max_price: float) -> List[Listing]:
        location = Validation.require_str(location, "location")
        max_price = Validation.is_positive_number(max_price, "max_price")

        sql = text("""
            SELECT id, seller_id, title, description, image_url, price, location,
                   created_at, is_sold, sold_to_id
            FROM listing
            WHERE is_sold = FALSE
              AND location LIKE :loc
              AND price <= :max_price
            ORDER BY created_at DESC, id DESC
        """)

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql, {"loc": f"%{location}%", "max_price": float(max_price)}).mappings().all()
                return [ListingMapper.from_mapping(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch unsold listings by location and max price.",
                details={"op": "get_unsold_by_location_and_max_price", "table": "listing"},
            ) from e

    @override
    def get_recent_unsold(self, limit: int = 50, offset: int = 0) -> List[Listing]:
        # Your Validation doesn't have "require_int but allow 0"? It does, and 0 is fine.
        limit = Validation.require_int(limit, "limit")
        offset = Validation.require_int(offset, "offset")

        sql = text("""
            SELECT id, seller_id, title, description, image_url, price, location,
                   created_at, is_sold, sold_to_id
            FROM listing
            WHERE is_sold = FALSE
            ORDER BY created_at DESC, id DESC
            LIMIT :limit OFFSET :offset
        """)

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql, {"limit": limit, "offset": offset}).mappings().all()
                return [ListingMapper.from_mapping(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch recent unsold listings.",
                details={"op": "get_recent_unsold", "table": "listing"},
            ) from e

    @override
    def find_unsold_by_title_keyword(self, keyword: str, limit: int = 50, offset: int = 0) -> List[Listing]:
        keyword = Validation.require_str(keyword, "keyword")
        limit = Validation.require_int(limit, "limit")
        offset = Validation.require_int(offset, "offset")

        sql = text("""
            SELECT id, seller_id, title, description, image_url, price, location,
                   created_at, is_sold, sold_to_id
            FROM listing
            WHERE is_sold = FALSE
              AND title LIKE :kw
            ORDER BY created_at DESC, id DESC
            LIMIT :limit OFFSET :offset
        """)

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql, {"kw": f"%{keyword}%", "limit": limit, "offset": offset}).mappings().all()
                return [ListingMapper.from_mapping(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch unsold listings by title keyword.",
                details={"op": "find_unsold_by_title_keyword", "table": "listing"},
            ) from e

    # -----------------------------
    # UPDATE
    # -----------------------------
    @override
    def update(self, listing: Listing) -> Listing:
        Validation.require_not_none(listing, "listing")

        listing_id = Validation.require_int(listing.id, "listing_id")
        title = Validation.require_str(listing.title, "title")
        description = Validation.require_str(listing.description, "description")
        price = Validation.is_positive_number(listing.price, "price")

        sql = text("""
            UPDATE listing
            SET title = :title,
                description = :description,
                image_url = :image_url,
                price = :price,
                location = :location
            WHERE id = :id
        """)

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {
                    "id": listing_id,
                    "title": title,
                    "description": description,
                    "image_url": (listing.image_url.strip() if listing.image_url else None),
                    "price": float(price),
                    "location": (listing.location.strip() if listing.location else None),
                })
                if int(result.rowcount or 0) == 0:
                    raise ListingNotFoundError(
                        message=f"Listing not found for id: {listing_id}",
                        details={"listing_id": listing_id},
                    )

            refreshed = self.get_by_id(listing_id)
            if refreshed is None:
                raise ListingNotFoundError(
                    message=f"Listing not found after update for id: {listing_id}",
                    details={"listing_id": listing_id},
                )
            return refreshed

        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to update listing.",
                details={"op": "update", "table": "listing"},
            ) from e

    @override
    def set_sold(self, listing_id: int, is_sold: bool, sold_to_id: Optional[int]) -> None:
        listing_id = Validation.require_int(listing_id, "listing_id")
        is_sold = Validation.is_boolean(is_sold, "is_sold")
        if sold_to_id is not None:
            sold_to_id = Validation.require_int(sold_to_id, "sold_to_id")

        sql = text("""
            UPDATE listing
            SET is_sold = :is_sold,
                sold_to_id = :sold_to_id
            WHERE id = :id
        """)

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {"id": listing_id, "is_sold": bool(is_sold), "sold_to_id": sold_to_id})
                if int(result.rowcount or 0) == 0:
                    raise ListingNotFoundError(
                        message=f"Listing not found for id: {listing_id}",
                        details={"listing_id": listing_id},
                    )
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to update listing sold state.",
                details={"op": "set_sold", "table": "listing"},
            ) from e

    @override
    def set_price(self, listing_id: int, price: float) -> None:
        listing_id = Validation.require_int(listing_id, "listing_id")
        price = Validation.is_positive_number(price, "price")

        sql = text("""
            UPDATE listing
            SET price = :price
            WHERE id = :id
        """)

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {"id": listing_id, "price": float(price)})
                if int(result.rowcount or 0) == 0:
                    raise ListingNotFoundError(
                        message=f"Listing not found for id: {listing_id}",
                        details={"listing_id": listing_id},
                    )
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to update listing price.",
                details={"op": "set_price", "table": "listing"},
            ) from e

    # -----------------------------
    # DELETE
    # -----------------------------
    @override
    def remove(self, listing_id: int) -> bool:
        listing_id = Validation.require_int(listing_id, "listing_id")

        sql = text("""
            DELETE FROM listing
            WHERE id = :id
        """)

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {"id": listing_id})
                return (result.rowcount or 0) > 0
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to delete listing.",
                details={"op": "remove", "table": "listing"},
            ) from e