# src/persistence/listing_db.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from src.db import DBUtility
from src.domain_models import Listing


class ListingDB(ABC):
    """
    Contract for Listing table persistence.

    IMPORTANT DESIGN RULES:
    - This layer is responsible ONLY for database access.
    - It does NOT contain business logic (authorization, ownership rules, etc.).
    - It does NOT decide HTTP responses.
    - It does NOT decide authentication logic.
    - It only performs CRUD + clearly-scoped queries.

    SECURITY / API SURFACE RULE:
    - Avoid "open-ended" search methods that accept many optional filters.
      Even if parameterized (SQL-safe), broad search surfaces often cause
      data-leak bugs at higher layers (e.g., forgetting authorization filters).
    - Prefer narrow, intention-revealing query methods that match real UI use-cases.

    Return conventions:
    - Methods that fetch a single row return Optional[Listing]:
        None is a valid state meaning "not found".
    - Methods that fetch multiple rows return List[Listing]:
        empty list is valid and MUST be returned when there are no results.


    ======================================================
    ERROR CONTRACT
    ======================================================

    All implementations MUST follow this error policy:

    1. Parameter validation failures:
       -> Raise ValidationError

    2. Record not found (when contract requires raising):
       -> Raise ListingNotFoundError

    3. Query-level SQL failures:
       -> Raise DatabaseQueryError

    4. Connection-level failures:
       -> Raised by DBUtility as DatabaseUnavailableError
          (Implementations should NOT catch/re-wrap those)
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

        Constraints / notes:
        - created_at is DB-managed (DEFAULT CURRENT_TIMESTAMP).
        - is_sold defaults to FALSE if not provided.
        - sold_to_id must remain NULL unless is_sold is TRUE (DB trigger enforces).
        - Never returns None.

        Raises:
            ValidationError:
                - Invalid seller_id, title, description, price
            DatabaseQueryError:
                - Constraint violation (FK, etc.)
                - SQL failure
            DatabaseUnavailableError:
                - Connection failure (from DBUtility)

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

        Raises:
            ValidationError:
                - listing_id is not int
            DatabaseQueryError:
                - SQL failure
            DatabaseUnavailableError:
                - Connection failure
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

         Raises:
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_seller_id(self, seller_id: int) -> List[Listing]:
        """
        Fetch all listings posted by a seller.

        Expected behavior:
        - Return empty list if none exist.
        - Must raise an exception if a database error occurs.

        Constraints / notes:
        - Higher layers should enforce that the caller is allowed
          to view this seller's listings (authorization).

        Raises:
            ValidationError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_buyer_id(self, buyer_id: int) -> List[Listing]:
        """
        Fetch all listings where this account is recorded as the buyer (sold_to_id).

        Expected behavior:
        - Return empty list if none exist.
        - Must raise an exception if a database error occurs.

        Constraints / notes:
        - Intended for "Purchased items" views.
        - Higher layers should enforce authorization.
        """
        raise NotImplementedError

    @abstractmethod
    def get_unsold(self) -> List[Listing]:
        """
        Fetch all unsold listings (is_sold = FALSE).

        Expected behavior:
        - Return empty list if none exist.
        - Must raise an exception if a database error occurs.

        Constraints / notes:
        - Public feed usage is common; consider adding pagination via get_recent_unsold().

        Raises:
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    # --------------------------------------------------
    # SAFER, PARAMETERIZED QUERIES (instead of open-ended search)
    # --------------------------------------------------

    @abstractmethod
    def get_recent_unsold(self, limit: int = 50, offset: int = 0) -> List[Listing]:
        """
        Fetch unsold listings with pagination (feed-style).

        Expected behavior:
        - Return empty list when no rows match.
        - Must raise an exception if a database error occurs.

        Constraints / notes:
        - limit and offset must be integers.
        - Higher layers may enforce max limit (e.g., limit <= 100).

        Raises:
            ValidationError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    @abstractmethod
    def get_unsold_by_location(self, location: str) -> List[Listing]:
        """
        Fetch unsold listings filtered by location (LIKE match).

        Expected behavior:
        - Return empty list when no rows match.
        - Must raise an exception if a database error occurs.

        Constraints / notes:
        - location must be a non-empty string.
        - Uses LIKE semantics (partial match), not exact equality.

        Raises:
            ValidationError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    @abstractmethod
    def get_unsold_by_max_price(self, max_price: float) -> List[Listing]:
        """
        Fetch unsold listings with price <= max_price.

        Expected behavior:
        - Return empty list when no rows match.
        - Must raise an exception if a database error occurs.

        Constraints / notes:
        - max_price must be a positive number (> 0).
        """
        raise NotImplementedError

    @abstractmethod
    def get_unsold_by_location_and_max_price(self, location: str, max_price: float) -> List[Listing]:
        """
        Fetch unsold listings filtered by location AND max_price.

        Expected behavior:
        - Return empty list when no rows match.
        - Must raise an exception if a database error occurs.

        Constraints / notes:
        - location must be non-empty string.
        - max_price must be positive number (> 0).
        - Intended to support common UI filters without exposing broad search.

        Raises:
            ValidationError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    @abstractmethod
    def find_unsold_by_title_keyword(self, keyword: str, limit: int = 50, offset: int = 0) -> List[Listing]:
        """
        Fetch unsold listings where title contains a keyword (LIKE match) with pagination.

        Expected behavior:
        - Return empty list when no rows match.
        - Must raise an exception if a database error occurs.

        Constraints / notes:
        - keyword must be a non-empty string.
        - Uses LIKE semantics (partial match).
        - Higher layers may enforce min keyword length (e.g., >= 2 chars).

        Raises:
            ValidationError
            DatabaseQueryError
            DatabaseUnavailableError
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
              raise ListingNotFoundError (or your chosen NotFound error)
        - Must raise an exception if a database error occurs.

        Constraints / notes:
        - This method does NOT enforce ownership/permissions.
          That belongs in the service/manager layer.
        - This method should NOT update is_sold/sold_to_id (use set_sold).

        Raises:
            ValidationError
            ListingNotFoundError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    @abstractmethod
    def set_sold(self, listing_id: int, is_sold: bool, sold_to_id: Optional[int]) -> None:
        """
        Update sold state and buyer.

        Expected behavior:
        - Update is_sold and sold_to_id.
        - If listing_id does not exist:
              raise ListingNotFoundError (or your chosen NotFound error)
        - Must raise an exception if a database error occurs.

        Constraints / notes:
        - DB trigger enforces:
            if is_sold is TRUE, sold_to_id must be set (non-null).
        - DB layer does not enforce the business rule "only seller can mark sold".
          Service/manager layer must enforce that.
        """
        raise NotImplementedError

    @abstractmethod
    def set_price(self, listing_id: int, price: float) -> None:
        """
        Update listing price.

        Expected behavior:
        - Update the price column for the listing_id.
        - If listing_id does not exist:
              raise ListingNotFoundError (or your chosen NotFound error)
        - Must raise an exception if a database error occurs.

        Constraints / notes:
        - price must be positive number (> 0).

        Raises:
            ValidationError
            ListingNotFoundError
            DatabaseQueryError
            DatabaseUnavailableError
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

        Constraints / notes:
        - ON DELETE CASCADE will remove offers/comments/rating under this listing.
        - Higher layers must enforce ownership/authorization before calling this.

        Raises:
            ValidationError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError