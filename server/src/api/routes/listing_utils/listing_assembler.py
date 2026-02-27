from __future__ import annotations

from dataclasses import dataclass

from src.api.converter.listing_converter import ListingResponse
from src.domain_models import Listing
from src.media_storage import MediaStorageUtility


@dataclass(frozen=True)
class ListingResponseAssembler:
    """
     Converts domain Listing -> API ListingResponse.

    Conventions:
    - listing.image_url (domain + DB) stores the MinIO object KEY
      e.g. "uploads/listings/<uuid>.png"
    - ListingResponse.image_url returns the raw key (for backward compatibility / debugging)
    - ListingResponse.minio_url returns a short-lived signed URL for clients

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
            except Exception:
                signed_url = None

        return ListingResponse(
            id=listing.id,
            seller_id=listing.seller_id,
            title=listing.title,
            description=listing.description,
            price=listing.price,

            image_url=listing.image_url,  # raw key
            minio_url=signed_url,  # signed URL

            location=listing.location,
            created_at=listing.created_at.isoformat() if listing.created_at else None,
            is_sold=listing.is_sold,
        )
