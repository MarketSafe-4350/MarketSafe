from pydantic import BaseModel, Field
from src.domain_models import Offer


class OfferCreate(BaseModel):
    """Data model for creating a new offer."""

    offered_price: float = Field(..., gt=0)
    location_offered: str | None = Field(default=None, max_length=120)

    def to_domain(self, listing_id: int, sender_id: int) -> Offer:
        return Offer(
            listing_id=listing_id,
            sender_id=sender_id,
            offered_price=self.offered_price,
            location_offered=self.location_offered,
        )


class OfferResponse(BaseModel):
    """Data model for offer response."""

    id: int | None = None
    listing_id: int
    sender_id: int
    offered_price: float
    location_offered: str | None = None
    seen: bool
    accepted: bool | None = None
    created_date: str | None = None

    @staticmethod
    def from_domain(offer: Offer) -> "OfferResponse":
        return OfferResponse(
            id=offer.id,
            listing_id=offer.listing_id,
            sender_id=offer.sender_id,
            offered_price=offer.offered_price,
            location_offered=offer.location_offered,
            seen=offer.seen,
            accepted=offer.accepted,
            created_date=offer.created_date.isoformat() if offer.created_date else None,
        )