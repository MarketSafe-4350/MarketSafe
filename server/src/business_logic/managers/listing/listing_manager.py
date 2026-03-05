from __future__ import annotations

from typing import List, Optional

from src.business_logic.managers.listing.abstract_listing_manager import IListingManager
from src.db.listing import ListingDB
from src.db.comment import CommentDB
from src.domain_models import Listing, Account
from src.utils import Validation, ListingNotFoundError, UnapprovedBehaviorError


class ListingManager(IListingManager):
    """
    Business layer implementation for listings.

    Responsibilities:
    - Orchestrate listing operations (no SQL here).
    - Validate inputs at the manager boundary (optional but recommended).
    - Combine aggregates when needed (Listing + Comments).

    Dependencies:
    - listing_db: ListingDB (required)
    - comment_db: CommentDB-like dependency (required for get_listing_with_comments)
    """

    def __init__(self, listing_db: ListingDB, comment_db: CommentDB) -> None:
        super().__init__(listing_db, comment_db)

    # -----------------------------
    # CREATE
    # -----------------------------
    def create_listing(self, listing: Listing) -> Listing:
        Validation.require_not_none(listing, "listing")
        # Domain constructor already enforces invariants, so we only sanity-check.
        return self._listing_db.add(listing)

    # -----------------------------
    # READ
    # -----------------------------
    def get_listing_by_id(self, listing_id: int) -> Optional[Listing]:
        listing_id = Validation.require_int(listing_id, "listing_id")
        return self._listing_db.get_by_id(listing_id)

    def list_listings(self) -> List[Listing]:
        return self._listing_db.get_all()

    def list_unsold_listings(self) -> List[Listing]:
        return self._listing_db.get_unsold()

    def list_recent_unsold(self, limit: int = 50, offset: int = 0) -> List[Listing]:
        limit = Validation.require_int(limit, "limit")
        offset = Validation.require_int(offset, "offset")
        return self._listing_db.get_recent_unsold(limit=limit, offset=offset)

    def list_unsold_by_location(self, location: str) -> List[Listing]:
        location = Validation.require_str(location, "location")
        return self._listing_db.get_unsold_by_location(location)

    def list_unsold_by_max_price(self, max_price: float) -> List[Listing]:
        max_price = Validation.is_positive_number(max_price, "max_price")
        return self._listing_db.get_unsold_by_max_price(max_price)

    def list_unsold_by_location_and_max_price(self, location: str, max_price: float) -> List[Listing]:
        location = Validation.require_str(location, "location")
        max_price = Validation.is_positive_number(max_price, "max_price")
        return self._listing_db.get_unsold_by_location_and_max_price(location, max_price)

    def find_unsold_by_title_keyword(self, keyword: str, limit: int = 50, offset: int = 0) -> List[Listing]:
        keyword = Validation.require_str(keyword, "keyword")
        limit = Validation.require_int(limit, "limit")
        offset = Validation.require_int(offset, "offset")
        return self._listing_db.find_unsold_by_title_keyword(keyword, limit=limit, offset=offset)

    def list_listings_by_seller(self, seller_id: int) -> List[Listing]:
        seller_id = Validation.require_int(seller_id, "seller_id")
        return self._listing_db.get_by_seller_id(seller_id)

    def list_listings_by_buyer(self, buyer_id: int) -> List[Listing]:
        buyer_id = Validation.require_int(buyer_id, "buyer_id")
        return self._listing_db.get_by_buyer_id(buyer_id)

    # -----------------------------
    # READ (orchestrated / aggregated)
    # -----------------------------
    def get_listing_with_comments(self, listing_id: int) -> Optional[Listing]:
        """
        Orchestration:
        - listing_db.get_by_id
        - comment_db.get_for_listing
        - attach listing.comments
        """
        listing_id = Validation.require_int(listing_id, "listing_id")

        listing = self._listing_db.get_by_id(listing_id)
        if listing is None:
            return None

        comments = self._comment_db.get_by_listing_id(listing_id)
        # Listing.comments setter validates list[Comment]
        listing.comments = comments
        return listing

    # -----------------------------
    # UPDATE
    # -----------------------------
    def update_listing(self, listing: Listing) -> Listing:
        Validation.require_not_none(listing, "listing")
        # listing.id must be set for updates (domain uses .id)
        Validation.require_int(listing.id, "listing_id")
        return self._listing_db.update(listing)

    def mark_listing_sold(self, actor: Account, listing: Listing, buyer: Account) -> None:
        # Basic null checks
        Validation.require_not_none(actor, "actor")
        Validation.require_not_none(listing, "listing")
        Validation.require_not_none(buyer, "buyer")

        actor_id = Validation.require_int(actor.id, "actor.id")
        buyer_id = Validation.require_int(buyer.id, "buyer.id")

        # Listing must be persisted
        if listing.id is None:
            raise ListingNotFoundError(
                message="Listing must be persisted before being marked as sold.",
                details={"listing_id": None},
            )

        # Authorization: only seller can mark sold
        if listing.seller_id != actor_id:
            raise UnapprovedBehaviorError(
                message="Only the seller can mark this listing as sold.",
                details={
                    "listing_id": listing.id,
                    "seller_id": listing.seller_id,
                    "actor_id": actor_id,
                },
            )

        # Prevent seller buying their own listing
        if listing.seller_id == buyer_id:
            raise UnapprovedBehaviorError(
                message="Seller cannot buy their own listing.",
                details={"listing_id": listing.id},
            )

        # Prevent double selling
        if listing.is_sold:
            raise UnapprovedBehaviorError(
                message="Listing is already sold.",
                details={"listing_id": listing.id},
            )

        listing.mark_sold(buyer_id)

        # Persist change
        self._listing_db.set_sold(
            listing_id=listing.id,
            is_sold=True,
            sold_to_id=buyer_id,
        )

    def update_listing_price(self, listing_id: int, price: float) -> None:
        listing_id = Validation.require_int(listing_id, "listing_id")
        price = Validation.is_positive_number(price, "price")
        self._listing_db.set_price(listing_id, price)

    # -----------------------------
    # DELETE
    # -----------------------------
    def delete_listing(self, listing_id: int) -> bool:
        listing_id = Validation.require_int(listing_id, "listing_id")
        return self._listing_db.remove(listing_id)