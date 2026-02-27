from pydantic import BaseModel
from src.domain_models import Listing


class ListingCreate(BaseModel):
    """Data model for creating a new listing."""

    title: str
    description: str
    price: float
    image_url: str | None = None
    location: str | None = None

    def to_domain(self, seller_id: int) -> Listing:
        return Listing(
            seller_id=seller_id,
            title=self.title,
            description=self.description,
            price=self.price,
            image_url=self.image_url,
            location=self.location,
        )


class ListingResponse(BaseModel):
    """Data model for listing response."""

    id: int | None = None
    seller_id: int
    title: str
    description: str
    price: float
    image_url: str | None = None
    location: str | None = None
    created_at: str | None = None
    is_sold: bool

    @staticmethod
    def from_domain(listing: Listing) -> "ListingResponse":
        return ListingResponse(
            id=listing.id,
            seller_id=listing.seller_id,
            title=listing.title,
            description=listing.description,
            price=listing.price,
            image_url=listing.image_url,
            location=listing.location,
            created_at=listing.created_at.isoformat() if listing.created_at else None,
            is_sold=listing.is_sold,
        )
