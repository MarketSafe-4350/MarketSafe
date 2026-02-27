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

    id: int | None = None
    seller_id: int
    title: str
    description: str
    price: float

    image_url: str | None = None      # raw DB value (MinIO key)
    minio_url: str | None = None      # signed temporary URL

    location: str | None = None
    created_at: str | None = None
    is_sold: bool
