from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Protocol

from src.db.listing import ListingDB
from src.domain_models import Listing, Account
from src.domain_models import Comment
from src.utils import Validation


class CommentDB(Protocol):
    """
    Planned persistence dependency for comments (not implemented yet).

    Expected method(s):
        - get_for_listing(listing_id: int) -> list[Comment]
    """

    def get_for_listing(self, listing_id: int) -> List[Comment]: ...


class IListingManager(ABC):
    """
    Listing business layer contract (manager/service).

    Responsibilities:
        - Contains business logic and orchestration.
        - Calls persistence layer (ListingDB, CommentDB) to read/write data.
        - Combines/aggregates domain objects when needed (e.g., listing + comments).
        - Decides which domain errors to raise (404/409/422/etc.).
        - Does NOT write SQL.

    Dependency contract:
        - Implementations are expected to be constructed with:
            - listing_db: ListingDB
            - comment_db: CommentDB  (not implemented yet)
        - comment_db is required for "get_listing_with_comments" orchestration.

    CommentDB expectation (planned interface):
        - comment_db.get_for_listing(listing_id: int) -> list[Comment]
            Returns comments for a listing (empty list if none).
            Raises DatabaseUnavailableError / DatabaseQueryError on DB failures.
            May raise ValidationError if listing_id invalid.

    Dependency contract:
        - listing_db: ListingDB (required)
        - comment_db: CommentDB (required for orchestration)
    """

    def __init__(self, listing_db: ListingDB, comment_db: CommentDB) -> None:
        Validation.require_not_none(listing_db, "listing_db")
        Validation.require_not_none(comment_db, "comment_db")
        self._listing_db = listing_db
        self._comment_db = comment_db

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------

    @abstractmethod
    def create_listing(self, listing: Listing) -> Listing:
        """
        PURPOSE:
            Create a new listing.

        EXPECTED BEHAVIOR:
            - Accept a Listing object (should already be structurally valid).
            - Enforce any listing creation business rules (if applicable).
            - Persist the listing using ListingDB.add().
            - Return the created Listing with generated database ID.

        RETURNS:
            Listing

        RAISES (typical):
            - ValidationError: if required fields are missing/invalid
            - DatabaseUnavailableError / DatabaseQueryError: on infrastructure failures
        """
        raise NotImplementedError

    # --------------------------------------------------
    # READ (simple)
    # --------------------------------------------------

    @abstractmethod
    def get_listing_by_id(self, listing_id: int) -> Optional[Listing]:
        """
        PURPOSE:
            Fetch a listing by its database ID.

        EXPECTED BEHAVIOR:
            - Return Listing if it exists.
            - Return None if not found.
            - Must NOT raise ListingNotFoundError for not found (reads are optional).

        IMPLEMENTATION NOTES:
            - Calls listing_db.get_by_id(listing_id)

        RETURNS:
            Listing | None

        RAISES (typical):
            - ValidationError: if listing_id invalid
            - DatabaseUnavailableError / DatabaseQueryError: on infrastructure failures
        """
        raise NotImplementedError

    @abstractmethod
    def list_listings(self) -> List[Listing]:
        """
        PURPOSE:
            List all listings.

        EXPECTED BEHAVIOR:
            - Return list of listings (empty if none).
            - Never return None.

        IMPLEMENTATION NOTES:
            - Calls listing_db.get_all()

        RETURNS:
            list[Listing]

        RAISES (typical):
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def list_unsold_listings(self) -> List[Listing]:
        """
        PURPOSE:
            List all unsold listings.

        EXPECTED BEHAVIOR:
            - Return list (empty if none).

        IMPLEMENTATION NOTES:
            - Calls listing_db.get_unsold()

        RETURNS:
            list[Listing]

        RAISES (typical):
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def list_recent_unsold(self, limit: int = 50, offset: int = 0) -> List[Listing]:
        """
        PURPOSE:
            Paginated feed of unsold listings.

        EXPECTED BEHAVIOR:
            - Return list (empty if none).
            - Validate limit/offset if manager chooses to enforce bounds.

        IMPLEMENTATION NOTES:
            - Calls listing_db.get_recent_unsold(limit, offset)

        RETURNS:
            list[Listing]

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def list_unsold_by_location(self, location: str) -> List[Listing]:
        """
        PURPOSE:
            Filter unsold listings by location.

        IMPLEMENTATION NOTES:
            - Calls listing_db.get_unsold_by_location(location)

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def list_unsold_by_max_price(self, max_price: float) -> List[Listing]:
        """
        PURPOSE:
            Filter unsold listings by max price.

        IMPLEMENTATION NOTES:
            - Calls listing_db.get_unsold_by_max_price(max_price)

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def list_unsold_by_location_and_max_price(
        self, location: str, max_price: float
    ) -> List[Listing]:
        """
        PURPOSE:
            Filter unsold listings by location and max price.

        IMPLEMENTATION NOTES:
            - Calls listing_db.get_unsold_by_location_and_max_price(location, max_price)

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def find_unsold_by_title_keyword(
        self, keyword: str, limit: int = 50, offset: int = 0
    ) -> List[Listing]:
        """
        PURPOSE:
            Find unsold listings by title keyword (LIKE).

        IMPLEMENTATION NOTES:
            - Calls listing_db.find_unsold_by_title_keyword(keyword, limit, offset)

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def list_listings_by_seller(self, seller_id: int) -> List[Listing]:
        """
        PURPOSE:
            List all listings for a seller.

        IMPLEMENTATION NOTES:
            - Calls listing_db.get_by_seller_id(seller_id)

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def list_listings_by_buyer(self, buyer_id: int) -> List[Listing]:
        """
        PURPOSE:
            List all listings purchased by a buyer (sold_to_id).

        IMPLEMENTATION NOTES:
            - Calls listing_db.get_by_buyer_id(buyer_id)

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    # --------------------------------------------------
    # READ (orchestrated / aggregated)
    # --------------------------------------------------

    @abstractmethod
    def get_listing_with_comments(self, listing_id: int) -> Optional[Listing]:
        """
        PURPOSE:
            Fetch a listing and attach its comments (aggregate root view).

        EXPECTED BEHAVIOR:
            - Fetch listing using listing_db.get_by_id(listing_id).
            - If listing is None -> return None.
            - Fetch comments using comment_db.get_for_listing(listing_id).
            - Attach comments:
                  listing.comments = comments
            - Return the listing.

        WHY THIS IS IN THE MANAGER:
            - This is orchestration/aggregation (business layer responsibility),
              not persistence-layer responsibility.
            - ListingDB should not depend on CommentDB or join across tables.

        DEPENDENCIES:
            - Requires comment_db to be provided to the manager implementation.
            - comment_db is not implemented yet, but this interface documents the expectation.

        RETURNS:
            Listing | None

        RAISES (typical):
            - ValidationError: invalid listing_id
            - DatabaseUnavailableError / DatabaseQueryError: DB failures from listing_db/comment_db
        """
        raise NotImplementedError

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    @abstractmethod
    def update_listing(self, listing: Listing) -> Listing:
        """
        PURPOSE:
            Update a listing (title/description/image_url/price/location).

        EXPECTED BEHAVIOR:
            - Requires listing.id to be present.
            - Calls listing_db.update(listing).
            - Raises ListingNotFoundError if listing does not exist.

        RETURNS:
            Updated Listing (re-read)

        RAISES (typical):
            - ValidationError
            - ListingNotFoundError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def mark_listing_sold(
        self, actor: Account, listing: Listing, buyer: Account
    ) -> None:
        """
         PURPOSE:
             Mark listing as sold to a buyer.

         EXPECTED BEHAVIOR:
             - Orchestrates sold state update.
             - Calls listing_db.set_sold(listing_id, True, buyer_id).

        Business Rules:
         - Actor must be the seller.
         - Listing must be persisted.
         - Buyer must be persisted.
         - Seller cannot buy their own listing.
         - Listing must not already be sold.

         RAISES (typical):
             - ValidationError
             - ListingNotFoundError
             - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def update_listing_price(self, listing_id: int, price: float) -> None:
        """
        PURPOSE:
            Update only the listing price.

        IMPLEMENTATION NOTES:
            - Calls listing_db.set_price(listing_id, price)

        RAISES (typical):
            - ValidationError
            - ListingNotFoundError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------

    @abstractmethod
    def delete_listing(self, listing_id: int) -> bool:
        """
        PURPOSE:
            Delete a listing.

        EXPECTED BEHAVIOR:
            - Return True if deleted.
            - Return False if not found (idempotent delete).
            - Must NOT raise ListingNotFoundError for missing row.

        IMPLEMENTATION NOTES:
            - Calls listing_db.remove(listing_id)

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError
