from pydantic import BaseModel


class ListingCreate(BaseModel):
    """Data model for creating a new listing."""

    title: str
    description: str
    price: float
    image_url: str | None = None
    location: str | None = None


class ListingResponse(BaseModel):
    """Data model for listing response."""

    title: str
    description: str
    price: float
    image_url: str | None = None
    location: str | None = None
    created_at: str | None = None
    is_sold: bool
