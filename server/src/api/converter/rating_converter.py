from pydantic import BaseModel, Field

from src.domain_models.rating import Rating


class RatingCreate(BaseModel):
    """Data model for creating a new rating."""

    transaction_rating: int = Field(..., ge=1, le=5)


class RatingResponse(BaseModel):
    """Data model for rating response."""

    id: int | None = None
    listing_id: int
    rater_id: int
    transaction_rating: int

    @staticmethod # pragma: no mutate
    def from_domain(rating: Rating) -> "RatingResponse":
        return RatingResponse(
            id=rating.id,
            listing_id=rating.listing_id,
            rater_id=rating.rater_id,
            transaction_rating=rating.transaction_rating,
        )
