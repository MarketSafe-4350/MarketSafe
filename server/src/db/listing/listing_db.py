from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Optional

from src.db import DBUtility
from src.domain_models import Listing


class ListingDB(ABC):
    """
    Contract for Listing table persistence.

    IMPORTANT DESIGN RULES:

    - This layer is responsible ONLY for database access.
    - It does NOT contain business logic.
    - It does NOT decide HTTP responses.
    - It does NOT decide authentication logic.
    - It only performs CRUD operations.

    Methods that query data return Optional[Listing]
    because "not found" is a valid database state.
    """

    def __init__(self, db: DBUtility) -> None:
        """
        The DBUtility instance must be injected.
        This allows:
        - Connection pooling reuse
        - Easier testing (mock DBUtility)
        - Clear separation of concerns
        """
        self._db = db

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------

    @abstractmethod
    def add(self, listing: Listing) -> Listing:
        """
        Insert a new listing row.

        Expected behavior:
        - Must insert the listing into the database.
        - Must return the created Listing with the generated ID.
        - Must raise an exception if:
            - seller_id does not exist (FK violation)
            - Database is unavailable
            - Any SQL error occurs

        Never returns None.
        """
        raise NotImplementedError

    # --------------------------------------------------
    # READ
    # --------------------------------------------------

    @abstractmethod
    def get_by_id(self, listing_id: int) -> Optional[Listing]:
        """
        Fetch listing by primary key.

        Expected behavior:
        - Return Listing if a row exists.
        - Return None if no row is found.
        - Must NOT raise exception for "not found".
        - Must raise exception if a database error occurs.
        """
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[Listing]:
        """
        Fetch all listings.

        Expected behavior:
        - Return an empty list if the table is empty.
        - Never return None.
        - Must raise an exception if a database error occurs.
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_seller_id(self, seller_id: int) -> List[Listing]:
        """
        Fetch all listings posted by a seller.

        Expected behavior:
        - Return empty list if none exist.
        - Must raise an exception if a database error occurs.
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_buyer_id(self, buyer_id: int) -> List[Listing]:
        """
        Fetch all listings where this account is recorded as the buyer (sold_to_id).

        Expected behavior:
        - Return empty list if none exist.
        - Must raise an exception if a database error occurs.
        """
        raise NotImplementedError

    @abstractmethod
    def get_unsold(self) -> List[Listing]:
        """
        Fetch all unsold listings (is_sold = FALSE).

        Expected behavior:
        - Return empty list if none exist.
        - Must raise an exception if a database error occurs.
        """
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        *,
        query: Optional[str] = None,
        location: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        is_sold: Optional[bool] = None,
        seller_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Listing]:
        """
        Flexible listing search.

        Notes:
        - This is still "DB access only": build WHERE clauses, bind params, return rows.
        - No ranking/business rules here; keep it simple and deterministic.

        Expected behavior:
        - Return empty list when no rows match.
        - Must raise an exception if a database error occurs.
        """
        raise NotImplementedError

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    @abstractmethod
    def update(self, listing: Listing) -> Listing:
        """
        Update listing fields (title, description, image_url, price, location, etc.).

        Expected behavior:
        - Must update the row for listing.id.
        - Must return the updated Listing (a re-read).
        - If listing.id does not exist:
              raise a NotFound exception
        - Must raise an exception if a database error occurs.
        """
        raise NotImplementedError

    @abstractmethod
    def set_sold(self, listing_id: int, is_sold: bool, sold_to_id: Optional[int]) -> None:
        """
        Update sold state and buyer.

        Expected behavior:
        - Update is_sold and sold_to_id.
        - If listing_id does not exist:
              raise a NotFound exception
        - Must raise an exception if a database error occurs.

        Notes:
        - The DB trigger enforces: if is_sold is TRUE, sold_to_id must be set.
        - This persistence method just performs the update.
        """
        raise NotImplementedError

    @abstractmethod
    def set_price(self, listing_id: int, price: Decimal) -> None:
        """
        Update listing price.

        Expected behavior:
        - Update the price column for the listing_id.
        - If listing_id does not exist:
              raise a NotFound exception
        - Must raise an exception if a database error occurs.
        """
        raise NotImplementedError

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------

    @abstractmethod
    def remove(self, listing_id: int) -> bool:
        """
        Delete a listing by ID.

        Expected behavior:
        - Return True if a row was deleted.
        - Return False if no row matched the ID.
        - Must NOT raise exception for "not found".
        - Must raise exception for database errors.

        Notes:
        - ON DELETE CASCADE will remove offers/comments/rating under this listing.
        """
        raise NotImplementedError

