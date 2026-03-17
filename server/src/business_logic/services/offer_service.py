from __future__ import annotations

from typing import List

from src.business_logic.managers.offer.abstract_offer_manager import IOffermanager
from src.business_logic.managers.listing.abstract_listing_manager import IListingManager
from src.business_logic.managers.account.abstract_account_manager import IAccountManager
from src.domain_models.offer import Offer
from src.utils import OfferNotFoundError, ListingNotFoundError, UnapprovedBehaviorError


class OfferService:
    """
    Service class for offer-related operations.

    Responsibilities:
    - Orchestrates cross-manager operations (offer + listing + account).
    - Delegates single-domain operations directly to OfferManager.
    - Does not write SQL or contain persistence logic.
    """

    def __init__(
        self,
        offer_manager: IOffermanager,
        listing_manager: IListingManager,
        account_manager: IAccountManager,
    ):
        self._offer_manager = offer_manager
        self._listing_manager = listing_manager
        self._account_manager = account_manager

    def create_offer(self, offer: Offer) -> Offer:
        return self._offer_manager.create_offer(offer)

    def get_offer_by_id(self, offer_id: int) -> Offer:
        return self._offer_manager.get_offer_by_id(offer_id)

    def get_offers_by_listing_id(self, listing_id: int) -> List[Offer]:
        return self._offer_manager.get_offers_by_listing_id(listing_id)

    def get_offers_by_sender_id(self, sender_id: int) -> List[Offer]:
        return self._offer_manager.get_offers_by_sender_id(sender_id)

    def get_offers_sellers(self, seller_id: int) -> List[Offer]:
        return self._offer_manager.get_offers_sellers(seller_id)

    def get_offer_sellers_pending(self, seller_id: int) -> List[Offer]:
        return self._offer_manager.get_offer_sellers_pending(seller_id)

    def get_offer_sellers_unseen(self, seller_id: int) -> List[Offer]:
        return self._offer_manager.get_offer_sellers_unseen(seller_id)

    def get_pending_offers_with_listing_by_sender(self, sender_id: int) -> List[Offer]:
        return self._offer_manager.get_pending_offers_with_listing_by_sender(sender_id)

    def set_offer_seen(self, offer_id: int) -> None:
        self._offer_manager.set_offer_seen(offer_id)

    def resolve_offer(self, offer_id: int, accepted: bool, actor_id: int) -> None:
        """
        Accept or decline an offer.

        When accepted=True, also marks the listing as sold via listing_manager,
        which enforces the full sold-state business rules (actor is seller,
        seller != buyer, listing not already sold).
        """
        offer = self._offer_manager.get_offer_by_id(offer_id)
        if offer is None:
            raise OfferNotFoundError(message=f"Offer {offer_id} not found.")

        self._offer_manager.set_offer_accepted(offer_id, accepted, actor_id)

        if accepted:
            actor = self._account_manager.get_account_by_id(actor_id)
            listing = self._listing_manager.get_listing_by_id(offer.listing_id)
            if listing is None:
                raise ListingNotFoundError(
                    message=f"Listing {offer.listing_id} not found."
                )
            buyer = self._account_manager.get_account_by_id(offer.sender_id)
            if buyer is None:
                raise UnapprovedBehaviorError(
                    message=f"Buyer account {offer.sender_id} not found."
                )

            self._listing_manager.mark_listing_sold(actor, listing, buyer)

    def delete_offer(self, offer_id: int) -> bool:
        return self._offer_manager.delete_offer(offer_id)
