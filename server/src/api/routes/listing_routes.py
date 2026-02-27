# src/api/routes/listing_routes.py
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from typing import List

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.security import HTTPBearer

from src.api.routes.listing_utils import ListingResponseAssembler, ListingImageUploader
from src.auth.dependencies import get_current_user_id
from src.business_logic.managers.listing.abstract_listing_manager import CommentDB
from src.business_logic.managers.listing.listing_manager import ListingManager
from src.business_logic.services.listing_service import ListingService
from src.db.listing.mysql.mysql_listing_db import MySQLListingDB
from src.db.utils.db_utils import DBUtility
from src.domain_models import Listing
from src.domain_models.comment import Comment
from src.api.converter.listing_converter import ListingCreate, ListingResponse
from src.api.dependencies import get_media_storage
from src.media_storage import MediaStorageUtility



router = APIRouter(prefix="/listings")
security = HTTPBearer()


class _NoOpCommentDB(CommentDB):
    """Temporary concrete comment DB stub so listing routes work before comments are wired."""

    def __init__(self, db):
        super().__init__(db)

    def add(self, comment: Comment) -> Comment:
        raise NotImplementedError("Comment persistence is not implemented yet.")

    def get_by_id(self, comment_id: int):
        return None

    def get_by_listing_id(self, listing_id: int):
        return []

    def get_by_author_id(self, author_id: int):
        return []

    def update_body(self, comment_id: int, body: str | None) -> None:
        raise NotImplementedError("Comment persistence is not implemented yet.")

    def remove(self, comment_id: int) -> bool:
        return False


def _get_service() -> ListingService:
    """
    Construct ListingService.

    Note:TODO: use Depends() provider.
    This mirrors your existing pattern. If you later switch to FastAPI dependency injection,
    you can convert this into a Depends() provider.
    """
    db = DBUtility.instance()
    listing_db = MySQLListingDB(db=db)
    # placeholder for now, will change when comment db is implemented
    comment_db = _NoOpCommentDB(db=db)
    listing_manager = ListingManager(listing_db=listing_db, comment_db=comment_db)
    return ListingService(listing_manager=listing_manager)


@router.get("", response_model=List[ListingResponse])
def get_all_listing(
    _: int = Depends(get_current_user_id),
    media: MediaStorageUtility = Depends(get_media_storage),
):
    """
    Get all listings.

    - Listing.image_url (DB) holds the MinIO object key.
    - ListingResponse.minio_url returns a short-lived signed URL for clients.
    """
    service = _get_service()
    assembler = ListingResponseAssembler(media)

    listings: List[Listing] = service.get_all_listing()
    return [assembler.to_response(l) for l in listings]


@router.get("/me", response_model=List[ListingResponse])
def get_my_listing(
    user_id: int = Depends(get_current_user_id),
    media: MediaStorageUtility = Depends(get_media_storage),
):
    """
    Get current user's listings.

    - Listing.image_url (DB) holds the MinIO object key.
    - ListingResponse.minio_url returns a short-lived signed URL for clients.
    """
    service = _get_service()
    assembler = ListingResponseAssembler(media)

    listings: List[Listing] = service.get_listing_by_user_id(user_id=user_id)
    return [assembler.to_response(l) for l in listings]

@router.get("/search", response_model=List[ListingResponse])
def search_listings(
    q: str = Query(..., min_length=1),
    _: int = Depends(get_current_user_id),
    media: MediaStorageUtility = Depends(get_media_storage),

):
    """Search listings using keyword(s) in title, description, or location."""
    service = _get_service()

    assembler = ListingResponseAssembler(media)
    listings: List[Listing] = service.search_listings(query=q)
    return [assembler.to_response(l) for l in listings]

@router.post("", response_model=ListingResponse)
def create_listing(
    request: ListingCreate,
    user_id: int = Depends(get_current_user_id),
    media: MediaStorageUtility = Depends(get_media_storage),
):
    """
    Create a listing from JSON.

    If request.image_url is provided, it must be a MinIO object key (not a signed URL).
    """
    service = _get_service()
    assembler = ListingResponseAssembler(media)

    listing: Listing = service.create_listing(
        seller_id=user_id,
        title=request.title,
        description=request.description,
        price=request.price,
        location=request.location,
        image_url=request.image_url,  # key stored in DB field image_url
    )

    return assembler.to_response(listing)


@router.post("/upload", response_model=ListingResponse)
async def create_listing_with_upload(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    location: str = Form(...),
    image: UploadFile | None = File(default=None),
    user_id: int = Depends(get_current_user_id),
    media: MediaStorageUtility = Depends(get_media_storage),
):
    """
    Create a listing using multipart/form-data.

    If an image is provided:
    - It is uploaded to MinIO bucket "media"
    - The returned object key is stored in Listing.image_url (DB)
    - The response returns minio_url (signed URL) for client use
    """
    service = _get_service()
    uploader = ListingImageUploader(media)
    assembler = ListingResponseAssembler(media)

    image_key = None
    if image is not None:
        try:
            image_key = uploader.save(image)
        finally:
            await image.close()

    listing: Listing = service.create_listing(
        seller_id=user_id,
        title=title,
        description=description,
        price=price,
        location=location,
        image_url=image_key,
    )

    return assembler.to_response(listing)


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(
    listing_id: int,
    user_id: int = Depends(get_current_user_id),
):
    """Deletes a listing owned by the current user."""
    service = _get_service()

    service.delete_listing(listing_id=listing_id, actor_user_id=user_id)
    return None
