from pydantic import BaseModel, Field

from src.domain_models import Listing
from src.minio.media_storage_utility import MediaStorageUtility


class ListingCreate(BaseModel):
    """Data model for creating a new listing."""

    title: str
    description: str
    price: float = Field(..., gt=0, le=99_999_999.99)
    image_url: str | None = None
    location: str | None = Field(default=None, max_length=120)

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
    def from_domain(
        listing: Listing,
        media_storage: MediaStorageUtility | None = None,
    ) -> "ListingResponse":
        image_url = listing.image_url

        if image_url and media_storage is not None:
            image_url = media_storage.public_url(image_url)

        return ListingResponse(
            id=listing.id,
            seller_id=listing.seller_id,
            title=listing.title,
            description=listing.description,
            price=listing.price,
            image_url=image_url,
            location=listing.location,
            created_at=listing.created_at.isoformat() if listing.created_at else None,
            is_sold=listing.is_sold,
        )