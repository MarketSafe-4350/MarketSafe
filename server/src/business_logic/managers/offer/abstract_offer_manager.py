from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from src.utils.validation import Validation
from src.db.offer.offer_db import OfferDB
from src.db.listing.listing_db import ListingDB
from src.domain_models.offer import Offer


class IOffermanager(ABC):
    """
    Offer business layer contract (manager/service).

    Responsibilities:
        - Contains business logic and orchestration.
        - Calls persistence layer (OfferDB) to read/write data.
        - Combines/aggregates domain objects when needed
          (e.g., offers + sender profiles, offers + listing details).
        - Decides which domain errors to raise (404/409/422/etc.).
        - Does NOT write SQL.

    Dependency contract:
        - offer_db: OfferDB (required)
        - listing_db: ListingDB (required for aggregated reads)
    """

    def __init__(self, offer_db: OfferDB, listing_db: ListingDB) -> None:
        Validation.require_not_none(offer_db, "offer_db")
        Validation.require_not_none(listing_db, "listing_db")
        self._offer_db = offer_db
        self._listing_db = listing_db

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------

    @abstractmethod
    def create_offer(self, offer: Offer) -> Offer:
        """
        PURPOSE:
            Create a new offer on a listing.

        EXPECTED BEHAVIOR:
            - Accept an Offer object (should already be structurally valid).
            - Enforce any business rules required before creation.
            - Persist the offer using OfferDB.add().
            - Return the created Offer with generated database ID.

        RETURNS:
            Offer

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
            - Domain-specific conflict/constraint errors if applicable
        """
        raise NotImplementedError

    # --------------------------------------------------
    # READ (simple)
    # --------------------------------------------------

    @abstractmethod
    def get_offer_by_id(self, offer_id: int) -> Optional[Offer]:
        """
        PURPOSE:
            Fetch an offer by its database ID.

        EXPECTED BEHAVIOR:
            - Return Offer if it exists.
            - Return None if not found.
            - Must NOT raise OfferNotFoundError for a normal read miss.

        RETURNS:
            Offer | None

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def get_all_offers(self) -> List[Offer]:
        """
        PURPOSE:
            List all offers across all listings.

        EXPECTED BEHAVIOR:
            - Return list of offers.
            - Return empty list if none exist.
            - Never return None.

        RETURNS:
            list[Offer]

        RAISES (typical):
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def get_offers_by_listing_id(self, listing_id: int) -> List[Offer]:
        """
        PURPOSE:
            List all offers made on a specific listing.

        EXPECTED BEHAVIOR:
            - Return list of offers.
            - Return empty list if none exist.
            - Never return None.

        RETURNS:
            list[Offer]

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def get_offers_by_sender_id(self, sender_id: int) -> List[Offer]:
        """
        PURPOSE:
            List all offers submitted by a specific sender/buyer.

        EXPECTED BEHAVIOR:
            - Return list of offers.
            - Return empty list if none exist.
            - Never return None.

        RETURNS:
            list[Offer]

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def get_accepted_offers_by_listing_id(self, listing_id: int) -> List[Offer]:
        """
        PURPOSE:
            List all accepted offers for a specific listing.

        EXPECTED BEHAVIOR:
            - Return list of offers where accepted=True.
            - Return empty list if none exist.
            - Never return None.

        RETURNS:
            list[Offer]

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def get_unseen_offers_by_listing_id(self, listing_id: int) -> List[Offer]:
        """
        PURPOSE:
            List all unseen offers on a specific listing.

        EXPECTED BEHAVIOR:
            - Return list of offers where seen=False.
            - Return empty list if none exist.
            - Never return None.

        RETURNS:
            list[Offer]

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def get_pending_offers_by_listing_id(self, listing_id: int) -> List[Offer]:
        """
        PURPOSE:
            List all pending (unresolved) offers on a specific listing.

        EXPECTED BEHAVIOR:
            - Return list of offers where accepted=None.
            - Return empty list if none exist.
            - Never return None.

        RETURNS:
            list[Offer]

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def get_offer_by_sender_and_listing(
        self, sender_id: int, listing_id: int
    ) -> Optional[Offer]:
        """
        PURPOSE:
            Fetch the offer made by a specific sender on a specific listing.

        EXPECTED BEHAVIOR:
            - Return Offer if one exists for the (sender_id, listing_id) pair.
            - Return None if not found.
            - Must NOT raise OfferNotFoundError for a normal read miss.

        RETURNS:
            Offer | None

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    # --------------------------------------------------
    # READ (aggregated)
    # --------------------------------------------------

    @abstractmethod
    def get_offers_sellers(self, seller_id: int) -> List[Offer]:
        """
        PURPOSE:
            Fetch all offers across all listings owned by a specific seller,
            each enriched with its associated listing details.

        EXPECTED BEHAVIOR:
            - Fetch all listings belonging to seller_id from ListingDB.
            - For each listing, fetch its offers using OfferDB.get_by_listing_id().
            - Attach the listing details to each Offer.
            - Return empty list if the seller has no listings or no offers.
            - Never return None.

        WHY THIS IS IN THE MANAGER:
            - Aggregating offers with listing data is orchestration
              (business layer responsibility), not persistence-layer responsibility.
            - OfferDB should not depend on ListingDB or join across tables.

        RETURNS:
            list[Offer]

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def get_offer_sellers_pending(self, seller_id: int) -> List[Offer]:
        """
        PURPOSE:
            Fetch all pending offers across all listings owned by a specific seller,
            each enriched with its associated listing details.

        EXPECTED BEHAVIOR:
            - Fetch all listings belonging to seller_id from ListingDB.
            - For each listing, fetch its pending offers using OfferDB.get_pending_by_listing_id().
            - Attach the listing details to each Offer.
            - Return empty list if the seller has no listings or no pending offers.
            - Never return None.

        WHY THIS IS IN THE MANAGER:
            - Aggregating offers with listing data is orchestration
              (business layer responsibility), not persistence-layer responsibility.
            - OfferDB should not depend on ListingDB or join across tables.

        RETURNS:
            list[Offer]

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def get_offer_sellers_unseen(self, seller_id: int) -> List[Offer]:
        """
        PURPOSE:
            Fetch all unseen offers across all listings owned by a specific seller,
            each enriched with its associated listing details.

        EXPECTED BEHAVIOR:
            - Fetch all listings belonging to seller_id from ListingDB.
            - For each listing, fetch its unseen offers using OfferDB.get_unseen_by_listing_id().
            - Attach the listing details to each Offer.
            - Return empty list if the seller has no listings or no unseen offers.
            - Never return None.

        WHY THIS IS IN THE MANAGER:
            - Aggregating offers with listing data is orchestration
              (business layer responsibility), not persistence-layer responsibility.
            - OfferDB should not depend on ListingDB or join across tables.

        RETURNS:
            list[Offer]

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def get_pending_offers_with_listing_by_sender(self, sender_id: int) -> List[Offer]:
        """
        PURPOSE:
            Fetch all pending offers made by a sender, each enriched with its
            associated listing details.

        EXPECTED BEHAVIOR:
            - Fetch pending offers (accepted=None) for the given sender.
            - For each offer, retrieve the associated listing from ListingDB.
            - Attach the listing details to each Offer.
            - Return empty list if none exist.
            - Never return None.

        WHY THIS IS IN THE MANAGER:
            - Aggregating offers with listing data is orchestration
              (business layer responsibility), not persistence-layer responsibility.
            - OfferDB should not depend on ListingDB or join across tables.

        RETURNS:
            list[Offer]

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    @abstractmethod
    def set_offer_seen(self, offer_id: int) -> None:
        """
        PURPOSE:
            Mark an offer as seen by the listing owner.

        EXPECTED BEHAVIOR:
            - Transition offer.seen from False to True.
            - Calls OfferDB.set_seen(offer_id).
            - Raises OfferNotFoundError if the offer does not exist.

        RETURNS:
            None

        RAISES (typical):
            - ValidationError
            - OfferNotFoundError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def set_offer_accepted(self, offer_id: int, accepted: bool, actor_id: int) -> None:
        """
        PURPOSE:
            Accept or decline an offer, transitioning it from pending to a resolved state.

        EXPECTED BEHAVIOR:
            - Validate that actor_id is the seller of the listing the offer belongs to.
            - Raise UnapprovedBehaviorError if actor is not the seller.
            - Raise OfferNotFoundError if the offer does not exist.
            - Raise UnapprovedBehaviorError if the offer is no longer pending.
            - Transition offer.accepted from None to True (accept) or False (decline).
            - If accepted=True:
                - Reject all other pending offers for the same listing.
                - Marking the listing as sold is handled by the service layer.

        RETURNS:
            None

        RAISES (typical):
            - ValidationError
            - OfferNotFoundError
            - ListingNotFoundError
            - UnapprovedBehaviorError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------

    @abstractmethod
    def delete_offer(self, offer_id: int) -> bool:
        """
        PURPOSE:
            Delete an offer by ID.

        EXPECTED BEHAVIOR:
            - Return True if deleted.
            - Return False if not found (idempotent delete).
            - Must NOT raise OfferNotFoundError for missing row.

        RETURNS:
            bool

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError
