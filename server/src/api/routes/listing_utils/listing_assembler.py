# src/api/assemblers/listing_response_assembler.py
from __future__ import annotations

from dataclasses import dataclass

from src.api.converter.listing_converter import ListingResponse
from src.domain_models import Listing
from src.media_storage import MediaStorageUtility
from src.utils import MediaNotFoundError, StorageUnavailableError


@dataclass(frozen=True)
class ListingResponseAssembler:
    """
    Converts domain Listing objects into API ListingResponse objects.

    Important:
    - Listing.image_url is treated as a MinIO object KEY (stored in DB)
      e.g. "uploads/listings/<uuid>.png"
    - The API response's image_url is a *signed URL* generated on demand.
      Signed URLs expire, so they are never stored in DB.
    """

    media: MediaStorageUtility
    expires_seconds: int = 300

    def to_response(self, listing: Listing) -> ListingResponse:
        """
        Convert Listing -> ListingResponse.
        If listing has an image key, it will be converted to a signed URL.

        Behavior on storage issues:
        - If image is missing or storage is down, image_url is returned as None.
          (You can change this to raise if you want strict behavior.)
        """
        signed_url = None

        if listing.image_url:
            try:
                signed_url = self.media.presigned_get_url(
                    listing.image_url,
                    expires_seconds=self.expires_seconds,
                )
            except (MediaNotFoundError, StorageUnavailableError):
                signed_url = None

        return ListingResponse(
            id=listing.id,
            seller_id=listing.seller_id,
            title=listing.title,
            description=listing.description,
            price=listing.price,
            image_url=signed_url,
            location=listing.location,
            created_at=listing.created_at.isoformat() if listing.created_at else None,
            is_sold=listing.is_sold,
        )