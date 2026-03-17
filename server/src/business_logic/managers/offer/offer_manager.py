from __future__ import annotations

from typing import List, Optional

from typing_extensions import override

from src.domain_models.listing import Listing
from src.business_logic.managers.offer.abstract_offer_manager import IOffermanager
from src.db.offer.offer_db import OfferDB
from src.db.listing.listing_db import ListingDB
from src.domain_models.offer import Offer
from src.utils import (
    Validation,
    ConflictError,
    UnapprovedBehaviorError,
    ListingNotFoundError,
    OfferNotFoundError,
)


class OfferManager(IOffermanager):
    """
    Concrete business/service implementation for offers.

    Responsibilities:
    - Validates inputs at the manager boundary.
    - Delegates persistence work to OfferDB and ListingDB.
    - Orchestrates aggregated reads across both DBs.
    - Does not write SQL.
    """

    def __init__(self, offer_db: OfferDB, listing_db: ListingDB) -> None:
        super().__init__(offer_db, listing_db)

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------

    @override
    def create_offer(self, offer: Offer) -> Offer:
        Validation.require_not_none(offer, "offer")

        listing: Optional[Listing] = self._listing_db.get_by_id(offer.listing_id)
        if listing is None:
            raise ListingNotFoundError(message=f"Listing {offer.listing_id} not found.")
        if listing.is_sold:
            raise UnapprovedBehaviorError(
                message="Cannot send an offer on a closed listing."
            )

        if listing.seller_id == offer.sender_id:
            raise UnapprovedBehaviorError(
                message="You cannot send an offer on your own listing."
            )

        existing: Optional[Offer] = self._offer_db.get_by_sender_and_listing(
            offer.sender_id, offer.listing_id
        )
        if existing is not None:
            if existing.is_pending:
                raise ConflictError(
                    message="You already have a pending offer on this listing. "
                    "Wait for it to be rejected before sending another."
                )
            if existing.accepted is True:
                raise UnapprovedBehaviorError(
                    message="Your offer on this listing was already accepted."
                )
            # existing.accepted is False (rejected) — allow re-offer

        return self._offer_db.add(offer)

    # --------------------------------------------------
    # READ (simple)
    # --------------------------------------------------

    @override
    def get_offer_by_id(self, offer_id: int) -> Optional[Offer]:
        offer_id = Validation.require_int(offer_id, "offer_id")
        return self._offer_db.get_by_id(offer_id)

    @override
    def get_all_offers(self) -> List[Offer]:
        return self._offer_db.get_all()

    @override
    def get_offers_by_listing_id(self, listing_id: int) -> List[Offer]:
        listing_id = Validation.require_int(listing_id, "listing_id")
        return self._offer_db.get_by_listing_id(listing_id)

    @override
    def get_offers_by_sender_id(self, sender_id: int) -> List[Offer]:
        sender_id = Validation.require_int(sender_id, "sender_id")
        return self._offer_db.get_by_sender_id(sender_id)

    @override
    def get_accepted_offers_by_listing_id(self, listing_id: int) -> List[Offer]:
        listing_id = Validation.require_int(listing_id, "listing_id")
        return self._offer_db.get_accepted_by_listing_id(listing_id)

    @override
    def get_unseen_offers_by_listing_id(self, listing_id: int) -> List[Offer]:
        listing_id = Validation.require_int(listing_id, "listing_id")
        return self._offer_db.get_unseen_by_listing_id(listing_id)

    @override
    def get_pending_offers_by_listing_id(self, listing_id: int) -> List[Offer]:
        listing_id = Validation.require_int(listing_id, "listing_id")
        return self._offer_db.get_pending_by_listing_id(listing_id)

    @override
    def get_offer_by_sender_and_listing(
        self, sender_id: int, listing_id: int
    ) -> Optional[Offer]:
        sender_id = Validation.require_int(sender_id, "sender_id")
        listing_id = Validation.require_int(listing_id, "listing_id")
        return self._offer_db.get_by_sender_and_listing(sender_id, listing_id)

    # --------------------------------------------------
    # READ (aggregated)
    # --------------------------------------------------

    @override
    def get_offers_sellers(self, seller_id: int) -> List[Offer]:
        seller_id = Validation.require_int(seller_id, "seller_id")
        listings = self._listing_db.get_by_seller_id(seller_id)
        offers = []
        for listing in listings:
            offers.extend(self._offer_db.get_by_listing_id(listing.id))
        return offers

    @override
    def get_offer_sellers_pending(self, seller_id: int) -> List[Offer]:
        seller_id = Validation.require_int(seller_id, "seller_id")
        listings = self._listing_db.get_by_seller_id(seller_id)
        offers = []
        for listing in listings:
            offers.extend(self._offer_db.get_pending_by_listing_id(listing.id))
        return offers

    @override
    def get_offer_sellers_unseen(self, seller_id: int) -> List[Offer]:
        seller_id = Validation.require_int(seller_id, "seller_id")
        listings = self._listing_db.get_by_seller_id(seller_id)
        offers = []
        for listing in listings:
            offers.extend(self._offer_db.get_unseen_by_listing_id(listing.id))
        return offers

    @override
    def get_pending_offers_with_listing_by_sender(self, sender_id: int) -> List[Offer]:
        sender_id = Validation.require_int(sender_id, "sender_id")
        all_offers = self._offer_db.get_by_sender_id(sender_id)
        return [offer for offer in all_offers if offer.is_pending]

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    @override
    def set_offer_seen(self, offer_id: int) -> None:
        offer_id = Validation.require_int(offer_id, "offer_id")
        self._offer_db.set_seen(offer_id)

    @override
    def set_offer_accepted(self, offer_id: int, accepted: bool, actor_id: int) -> None:
        offer_id = Validation.require_int(offer_id, "offer_id")
        actor_id = Validation.require_int(actor_id, "actor_id")
        Validation.is_boolean(accepted, "accepted")

        offer = self._offer_db.get_by_id(offer_id)
        if offer is None:
            raise OfferNotFoundError(message=f"Offer {offer_id} not found.")

        listing = self._listing_db.get_by_id(offer.listing_id)
        if listing is None:
            raise ListingNotFoundError(message=f"Listing {offer.listing_id} not found.")

        if listing.seller_id != actor_id:
            raise UnapprovedBehaviorError(
                message="Only the seller of the listing can accept or decline offers."
            )

        if not offer.is_pending:
            raise UnapprovedBehaviorError(
                message="This offer has already been resolved."
            )

        self._offer_db.set_accepted(offer_id, accepted)

        if accepted:
            pending_offers = self._offer_db.get_pending_by_listing_id(offer.listing_id)
            for other in pending_offers:
                if other.id != offer_id:
                    self._offer_db.set_accepted(other.id, False)

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------

    @override
    def delete_offer(self, offer_id: int) -> bool:
        offer_id = Validation.require_int(offer_id, "offer_id")
        return self._offer_db.remove(offer_id)
