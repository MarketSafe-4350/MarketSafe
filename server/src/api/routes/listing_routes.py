from fastapi import APIRouter
from src.domain_models import Listing
from src.api.converter.listing_converter import ListingCreate, ListingResponse
from src.business_logic.services.listing_service import ListingService


def create_listing_router(service: ListingService) -> APIRouter:
    router = APIRouter(prefix="/listings")

    @router.post("", response_model=ListingResponse)
    def create_listing(request: ListingCreate):
        """Creates a new listing.

        Args:
            request (ListingCreate): The listing creation request data.

        Returns:
            ListingResponse: The response model for the newly created listing.
        """
        listing: Listing = service.create_listing(
            seller_id=1,  # hardcoded for now, will implement auth later
            title=request.title,
            description=request.description,
            price=request.price,
            location=request.location,
            image_url=request.image_url,
        )

        return ListingResponse(
            title=listing.title,
            description=listing.description,
            price=listing.price,
            image_url=listing.image_url,
            location=listing.location,
            created_at=listing.created_at.isoformat() if listing.created_at else None,
            is_sold=listing.is_sold,
        )

    return router
