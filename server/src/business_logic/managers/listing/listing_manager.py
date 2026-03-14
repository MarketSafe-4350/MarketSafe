from __future__ import annotations

from typing import List, Optional

from typing_extensions import override

from src.business_logic.managers.listing.abstract_listing_manager import IListingManager
from src.db.listing import ListingDB
from src.db.comment import CommentDB
from src.db.rating import BaseRatingDB
from src.domain_models import Listing, Account
from src.utils import Validation, ListingNotFoundError, UnapprovedBehaviorError, ConfigurationError


class ListingManager(IListingManager):
    """
       Business layer implementation for listings.

       Responsibilities:
       - Orchestrate listing operations (no SQL here).
       - Validate inputs at the manager boundary (optional but recommended).
       - Combine aggregates when needed (Listing + Comments + Rating).

       Dependencies:
       - listing_db: ListingDB (required)
       - comment_db: CommentDB (required for get_listing_with_comments)
       - rating_db: BaseRatingDB (optional, used for rating enrichment)
       """

    def __init__(
            self,
            listing_db: ListingDB,
            comment_db: CommentDB,
            rating_db: Optional[BaseRatingDB] = None,
    ) -> None:
        super().__init__(listing_db, comment_db, rating_db)

        # -----------------------------
        # CREATE
        # -----------------------------

    @override
    def create_listing(self, listing: Listing) -> Listing:
        Validation.require_not_none(listing, "listing")
        created = self._listing_db.add(listing)
        return self._populate_rating_if_available(created)

    # -----------------------------
    # READ
    # -----------------------------
    @override
    def get_listing_by_id(self, listing_id: int) -> Optional[Listing]:
        listing_id = Validation.require_int(listing_id, "listing_id")
        listing = self._listing_db.get_by_id(listing_id)
        return self._populate_rating_if_available(listing)

    @override
    def list_listings(self) -> List[Listing]:
        listings = self._listing_db.get_all()
        return self._populate_ratings_if_available(listings)

    @override
    def list_unsold_listings(self) -> List[Listing]:
        listings = self._listing_db.get_unsold()
        return self._populate_ratings_if_available(listings)

    @override
    def list_recent_unsold(self, limit: int = 50, offset: int = 0) -> List[Listing]:
        limit = Validation.require_int(limit, "limit")
        offset = Validation.require_int(offset, "offset")
        listings = self._listing_db.get_recent_unsold(limit=limit, offset=offset)
        return self._populate_ratings_if_available(listings)

    @override
    def list_unsold_by_location(self, location: str) -> List[Listing]:
        location = Validation.require_str(location, "location")
        listings = self._listing_db.get_unsold_by_location(location)
        return self._populate_ratings_if_available(listings)

    @override
    def list_unsold_by_max_price(self, max_price: float) -> List[Listing]:
        max_price = Validation.is_positive_number(max_price, "max_price")
        listings = self._listing_db.get_unsold_by_max_price(max_price)
        return self._populate_ratings_if_available(listings)

    @override
    def list_unsold_by_location_and_max_price(self, location: str, max_price: float) -> List[Listing]:
        location = Validation.require_str(location, "location")
        max_price = Validation.is_positive_number(max_price, "max_price")
        listings = self._listing_db.get_unsold_by_location_and_max_price(location, max_price)
        return self._populate_ratings_if_available(listings)

    @override
    def find_unsold_by_title_keyword(self, keyword: str, limit: int = 50, offset: int = 0) -> List[Listing]:
        keyword = Validation.require_str(keyword, "keyword")
        limit = Validation.require_int(limit, "limit")
        offset = Validation.require_int(offset, "offset")
        listings = self._listing_db.find_unsold_by_title_keyword(keyword, limit=limit, offset=offset)
        return self._populate_ratings_if_available(listings)

    @override
    def list_listings_by_seller(self, seller_id: int) -> List[Listing]:
        seller_id = Validation.require_int(seller_id, "seller_id")
        listings = self._listing_db.get_by_seller_id(seller_id)
        return self._populate_ratings_if_available(listings)

    @override
    def list_listings_by_buyer(self, buyer_id: int) -> List[Listing]:
        buyer_id = Validation.require_int(buyer_id, "buyer_id")
        listings = self._listing_db.get_by_buyer_id(buyer_id)
        return self._populate_ratings_if_available(listings)

    # -----------------------------
    # READ (orchestrated / aggregated)
    # -----------------------------
    @override
    def get_listing_with_comments(self, listing_id: int) -> Optional[Listing]:
        """
        Orchestration:
        - listing_db.get_by_id
        - comment_db.get_by_listing_id
        - attach listing.comments
        - optionally attach listing.rating if RatingDB exists
        """
        listing_id = Validation.require_int(listing_id, "listing_id")

        listing = self._listing_db.get_by_id(listing_id)
        if listing is None:
            return None

        comments = self._comment_db.get_by_listing_id(listing_id)
        listing.comments = comments

        return self._populate_rating_if_available(listing)

    @override
    def fill_listing_rating_value(self, listing: Listing) -> Listing:
        """
        Populate rating on an existing Listing instance.

        Raises:
        - ConfigurationError if RatingDB dependency is missing
        """
        Validation.require_not_none(listing, "listing")

        if self._rating_db is None:
            raise ConfigurationError(
                message="RatingDB dependency is required for fill_listing_rating_value().",
                details={"missing_dependency": "BaseRatingDB"},
            )

        if listing.id is None:
            return listing

        listing.rating = self._rating_db.get_by_listing_id(listing.id)
        return listing

    @override
    def get_listing_with_rating_by_id(self, listing_id: int) -> Optional[Listing]:
        """
        Fetch listing by id and populate rating.

        Raises:
        - ConfigurationError if RatingDB dependency is missing
        """
        listing_id = Validation.require_int(listing_id, "listing_id")

        if self._rating_db is None:
            raise ConfigurationError(
                message="RatingDB dependency is required for get_listing_with_rating_by_id().",
                details={"missing_dependency": "BaseRatingDB"},
            )

        listing = self._listing_db.get_by_id(listing_id)
        if listing is None:
            return None

        return self.fill_listing_rating_value(listing)

    @override
    def get_listing_with_comments_and_rating(self, listing_id: int) -> Optional[Listing]:
        """
        Fetch listing by id and populate both comments and rating.

        Raises:
        - ConfigurationError if RatingDB dependency is missing
        """
        listing_id = Validation.require_int(listing_id, "listing_id")

        if self._rating_db is None:
            raise ConfigurationError(
                message="RatingDB dependency is required for get_listing_with_comments_and_rating().",
                details={"missing_dependency": "BaseRatingDB"},
            )

        listing = self._listing_db.get_by_id(listing_id)
        if listing is None:
            return None

        listing.comments = self._comment_db.get_by_listing_id(listing_id)
        return self.fill_listing_rating_value(listing)

    # -----------------------------
    # UPDATE
    # -----------------------------
    @override
    def update_listing(self, listing: Listing) -> Listing:
        Validation.require_not_none(listing, "listing")
        Validation.require_int(listing.id, "listing_id")
        updated = self._listing_db.update(listing)
        return self._populate_rating_if_available(updated)

    @override
    def mark_listing_sold(self, actor: Account, listing: Listing, buyer: Account) -> None:
        Validation.require_not_none(actor, "actor")
        Validation.require_not_none(listing, "listing")
        Validation.require_not_none(buyer, "buyer")

        actor_id = Validation.require_int(actor.id, "actor.id")
        buyer_id = Validation.require_int(buyer.id, "buyer.id")

        if listing.id is None:
            raise ListingNotFoundError(
                message="Listing must be persisted before being marked as sold.",
                details={"listing_id": None},
            )

        if listing.seller_id != actor_id:
            raise UnapprovedBehaviorError(
                message="Only the seller can mark this listing as sold.",
                details={
                    "listing_id": listing.id,
                    "seller_id": listing.seller_id,
                    "actor_id": actor_id,
                },
            )

        if listing.seller_id == buyer_id:
            raise UnapprovedBehaviorError(
                message="Seller cannot buy their own listing.",
                details={"listing_id": listing.id},
            )

        if listing.is_sold:
            raise UnapprovedBehaviorError(
                message="Listing is already sold.",
                details={"listing_id": listing.id},
            )

        listing.mark_sold(buyer_id)

        self._listing_db.set_sold(
            listing_id=listing.id,
            is_sold=True,
            sold_to_id=buyer_id,
        )

    @override
    def update_listing_price(self, listing_id: int, price: float) -> None:
        listing_id = Validation.require_int(listing_id, "listing_id")
        price = Validation.is_positive_number(price, "price")
        self._listing_db.set_price(listing_id, price)

    # -----------------------------
    # DELETE
    # -----------------------------
    @override
    def delete_listing(self, listing_id: int) -> bool:
        listing_id = Validation.require_int(listing_id, "listing_id")
        return self._listing_db.remove(listing_id)

    # ==================================================
    # INTERNAL HELPERS
    # ==================================================

    def _populate_rating_if_available(self, listing: Optional[Listing]) -> Optional[Listing]:
        """
        Populate listing.rating if RatingDB is available.

        Behavior:
        - If listing is None -> return None
        - If rating_db is not configured -> return listing unchanged
        - If listing is not persisted -> return listing unchanged
        - If listing has no rating -> keep listing.rating as None
        """
        if listing is None:
            return None

        if self._rating_db is None:
            return listing

        if listing.id is None:
            return listing

        listing.rating = self._rating_db.get_by_listing_id(listing.id)
        return listing

    def _populate_ratings_if_available(self, listings: List[Listing]) -> List[Listing]:
        if self._rating_db is None:
            return listings

        for listing in listings:
            self._populate_rating_if_available(listing)

        return listings
