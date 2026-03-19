from fastapi import APIRouter, Depends, HTTPException
from typing import List

from fastapi.security import HTTPBearer

from src.auth.dependencies import get_current_user_id
from src.api.dependencies import get_offer_service
from src.business_logic.services import OfferService
from src.api.converter.offer_converter import OfferCreate, OfferResponse
from src.domain_models import Offer


router = APIRouter()
security = HTTPBearer()

# -------------------------------------------------------
# 1. create_offer
# -------------------------------------------------------
@router.post("/listings/{listing_id}/offer", response_model=OfferResponse)
def create_offer(
    listing_id: int,
    offer: OfferCreate,
    user_id: int = Depends(get_current_user_id),
    offer_service: OfferService = Depends(get_offer_service),
):
    domain_offer = Offer(
        listing_id=listing_id,
        sender_id=user_id,
        offered_price=offer.offered_price,
        location_offered=offer.location_offered,
    )

    created_offer = offer_service.create_offer(domain_offer)
    return OfferResponse.from_domain(created_offer)


# -------------------------------------------------------
# 2. get_offer_by_id
# -------------------------------------------------------
@router.get("/offers/{offer_id}", response_model=OfferResponse)
def get_offer_by_id(
    offer_id: int,
    _: int = Depends(get_current_user_id),
    offer_service: OfferService = Depends(get_offer_service),
):
    offer = offer_service.get_offer_by_id(offer_id)
    return OfferResponse.from_domain(offer)


# -------------------------------------------------------
# 3. get_offers_by_listing_id
# -------------------------------------------------------
@router.get("/listings/{listing_id}/offer", response_model=List[OfferResponse])
def get_offers_by_listing(
    listing_id: int,
    _: int = Depends(get_current_user_id),
    offer_service: OfferService = Depends(get_offer_service),
):
    offers = offer_service.get_offers_by_listing_id(listing_id)
    return [OfferResponse.from_domain(o) for o in offers]


# -------------------------------------------------------
# 4. get_offers_by_sender_id
# -------------------------------------------------------
@router.get("/accounts/offers/sent", response_model=List[OfferResponse])
def get_offers_sent(
    user_id: int = Depends(get_current_user_id),
    offer_service: OfferService = Depends(get_offer_service),
):
    offers = offer_service.get_offers_by_sender_id(user_id)
    return [OfferResponse.from_domain(o) for o in offers]


# -------------------------------------------------------
# 5. get_offers_sellers
# -------------------------------------------------------
@router.get("/accounts/offers/received", response_model=List[OfferResponse])
def get_offers_received(
    user_id: int = Depends(get_current_user_id),
    offer_service: OfferService = Depends(get_offer_service),
):
    offers = offer_service.get_offers_sellers(user_id)
    return [OfferResponse.from_domain(o) for o in offers]


# -------------------------------------------------------
# 6. get_offer_sellers_pending
# -------------------------------------------------------
@router.get("/accounts/offers/received/pending", response_model=List[OfferResponse])
def get_pending_received_offers(
    user_id: int = Depends(get_current_user_id),
    offer_service: OfferService = Depends(get_offer_service),
):
    offers = offer_service.get_offer_sellers_pending(user_id)
    return [OfferResponse.from_domain(o) for o in offers]


# -------------------------------------------------------
# 7. get_offer_sellers_unseen
# -------------------------------------------------------
@router.get("/accounts/offers/received/unseen", response_model=List[OfferResponse])
def get_unseen_received_offers(
    user_id: int = Depends(get_current_user_id),
    offer_service: OfferService = Depends(get_offer_service),
):
    offers = offer_service.get_offer_sellers_unseen(user_id)
    return [OfferResponse.from_domain(o) for o in offers]


# -------------------------------------------------------
# 8. get_pending_offers_with_listing_by_sender
# -------------------------------------------------------
@router.get("/accounts/offers/sent/pending", response_model=List[OfferResponse])
def get_pending_sent_offers(
    user_id: int = Depends(get_current_user_id),
    offer_service: OfferService = Depends(get_offer_service),
):
    offers = offer_service.get_pending_offers_with_listing_by_sender(user_id)
    return [OfferResponse.from_domain(o) for o in offers]


# -------------------------------------------------------
# 9. set_offer_seen
# -------------------------------------------------------
@router.patch("/offers/{offer_id}/seen")
def mark_offer_seen(
    offer_id: int,
    _: int = Depends(get_current_user_id),
    offer_service: OfferService = Depends(get_offer_service),
):
    offer_service.set_offer_seen(offer_id)
    return {"message": "Offer marked as seen"}


# -------------------------------------------------------
# 10. resolve_offer
# -------------------------------------------------------
@router.post("/offers/{offer_id}/resolve")
def resolve_offer(
    offer_id: int,
    accepted: bool,
    user_id: int = Depends(get_current_user_id),
    offer_service: OfferService = Depends(get_offer_service),
):
    offer_service.resolve_offer(offer_id, accepted, user_id)
    return {"message": "Offer resolved"}


# -------------------------------------------------------
# 11. delete_offer
# -------------------------------------------------------
@router.delete("/offers/{offer_id}")
def delete_offer(
    offer_id: int,
    _: int = Depends(get_current_user_id),
    offer_service: OfferService = Depends(get_offer_service),
):
    success = offer_service.delete_offer(offer_id)
    return {"deleted": success}