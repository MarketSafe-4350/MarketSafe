import uuid
from pathlib import Path
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.security import HTTPBearer

from src.auth.dependencies import get_current_user_id
from src.domain_models import Listing
from src.domain_models.comment import Comment
from src.api.converter.listing_converter import ListingCreate, ListingResponse
from src.api.converter.comment_converter import CommentCreate, CommentResponse
from src.api.converter.rating_converter import RatingCreate, RatingResponse
from src.business_logic.services import (
    ListingService,
    CommentService,
    CommentWithAuthor,
)
from src.api.dependencies import (
    get_listing_service,
    get_comment_service,
    get_media_storage,
)
from src.minio.media_storage_utility import MediaStorageUtility

router = APIRouter(prefix="/listings")


def _normalized_image_extension(upload: UploadFile) -> str:
    allowed = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix in allowed:
        return suffix

    by_content_type = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }
    return by_content_type.get(upload.content_type or "", ".jpg")


async def _upload_listing_image(
    upload: UploadFile,
    media_storage: MediaStorageUtility,
) -> str:
    if not (upload.content_type or "").startswith("image/"):
        raise ValueError("Uploaded file must be an image.")

    ext = _normalized_image_extension(upload)
    key = f"listings/{uuid.uuid4().hex}{ext}"
    data = await upload.read()

    return media_storage.upload_bytes(
        key=key,
        data=data,
        content_type=upload.content_type or "application/octet-stream",
    )


@router.get("", response_model=List[ListingResponse])
def get_all_listing(
    _: int = Depends(get_current_user_id),
    listing_service: ListingService = Depends(get_listing_service),
    media_storage: MediaStorageUtility = Depends(get_media_storage),
):
    listings: List[Listing] = listing_service.get_all_listing()
    return [ListingResponse.from_domain(listing, media_storage) for listing in listings]


@router.get("/me", response_model=List[ListingResponse])
def get_my_listing(
    user_id: int = Depends(get_current_user_id),
    listing_service: ListingService = Depends(get_listing_service),
    media_storage: MediaStorageUtility = Depends(get_media_storage),
):
    listings: List[Listing] = listing_service.get_listing_by_user_id(user_id=user_id)
    return [ListingResponse.from_domain(listing, media_storage) for listing in listings]


@router.get("/search", response_model=List[ListingResponse])
def search_listings(
    q: str = Query(..., min_length=1),
    _: int = Depends(get_current_user_id),
    listing_service: ListingService = Depends(get_listing_service),
    media_storage: MediaStorageUtility = Depends(get_media_storage),
):
    listings = listing_service.search_listings(query=q)
    return [ListingResponse.from_domain(listing, media_storage) for listing in listings]


@router.get("/seller/{seller_id}", response_model=List[ListingResponse])
def get_listings_by_seller(
    seller_id: int,
    _: int = Depends(get_current_user_id),
    listing_service: ListingService = Depends(get_listing_service),
    media_storage: MediaStorageUtility = Depends(get_media_storage),
):
    listings: List[Listing] = listing_service.get_listing_by_user_id(user_id=seller_id)
    return [ListingResponse.from_domain(listing, media_storage) for listing in listings]


@router.post("", response_model=ListingResponse)
def create_listing(
    request: ListingCreate,
    user_id: int = Depends(get_current_user_id),
    listing_service: ListingService = Depends(get_listing_service),
    media_storage: MediaStorageUtility = Depends(get_media_storage),
):
    listing: Listing = listing_service.create_listing(
        seller_id=user_id,
        title=request.title,
        description=request.description,
        price=request.price,
        location=request.location,
        image_url=request.image_url,
    )

    return ListingResponse.from_domain(listing, media_storage)


@router.post("/upload", response_model=ListingResponse)
async def create_listing_with_upload(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    location: str = Form(...),
    image: UploadFile | None = File(default=None),
    user_id: int = Depends(get_current_user_id),
    listing_service: ListingService = Depends(get_listing_service),
    media_storage: MediaStorageUtility = Depends(get_media_storage),
):
    image_key = None

    if image is not None:
        try:
            image_key = await _upload_listing_image(image, media_storage)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        finally:
            await image.close()

    listing: Listing = listing_service.create_listing(
        seller_id=user_id,
        title=title,
        description=description,
        price=price,
        location=location,
        image_url=image_key,
    )

    return ListingResponse.from_domain(listing, media_storage)


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(
    listing_id: int,
    user_id: int = Depends(get_current_user_id),
    listing_service: ListingService = Depends(get_listing_service),
):
    listing_service.delete_listing(listing_id=listing_id, actor_user_id=user_id)
    return None


@router.get("/{listing_id}/comments", response_model=List[CommentResponse])
def get_listing_comment(
    listing_id: int,
    user_id: int = Depends(get_current_user_id),
    comment_service: CommentService = Depends(get_comment_service),
):
    comments_author: List[CommentWithAuthor] = comment_service.get_all_comments_listing(
        listing_id=listing_id
    )

    return [
        CommentResponse.from_domain(
            comment=c.comment,
            author=c.author,
        )
        for c in comments_author
    ]


@router.post("/{listing_id}/ratings", response_model=RatingResponse)
def rate_listing(
    listing_id: int,
    rating_request: RatingCreate,
    user_id: int = Depends(get_current_user_id),
    listing_service: ListingService = Depends(get_listing_service),
):
    rating = listing_service.rate_listing(
        listing_id=listing_id,
        rater_id=user_id,
        transaction_rating=rating_request.transaction_rating,
    )
    return RatingResponse.from_domain(rating)


@router.get("/{listing_id}/ratings", response_model=RatingResponse | None)
def get_listing_rating(
    listing_id: int,
    _: int = Depends(get_current_user_id),
    listing_service: ListingService = Depends(get_listing_service),
):
    rating = listing_service.get_listing_rating(listing_id)
    if rating is None:
        return None

    return RatingResponse.from_domain(rating)


@router.post("/{listing_id}/comments", response_model=CommentResponse)
def create_listing_comment(
    listing_id: int,
    comment_request: CommentCreate,
    user_id: int = Depends(get_current_user_id),
    comment_service: CommentService = Depends(get_comment_service),
):
    comment_domain: Comment = comment_request.to_domain(
        listing_id=listing_id,
        author_id=user_id,
    )

    item: CommentWithAuthor = comment_service.create_comment(
        actor_id=user_id,
        listing_id=listing_id,
        comment=comment_domain,
    )

    return CommentResponse.from_domain(
        comment=item.comment,
        author=item.author,
    )
