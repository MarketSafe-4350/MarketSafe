import shutil
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from typing import List
from src.auth.dependencies import get_current_user_id
from src.business_logic.managers.listing import ListingManager
from src.business_logic.managers.comment import CommentManager
from src.db.listing.mysql import MySQLListingDB
from src.db.comment.mysql import MySQLCommentDB
from src.business_logic.managers.listing.abstract_listing_manager import CommentDB
from src.db.utils.db_utils import DBUtility
from src.db.email_verification_token.mysql.mysql_email_verification_token_db import (
    MySQLEmailVerificationTokenDB,
)
from src.domain_models import Listing
from src.api.converter.listing_converter import ListingCreate, ListingResponse
from src.api.converter.comment_converter import CommentCreate, CommentResponse
from src.business_logic.services import ListingService, CommentService
from src.domain_models.comment import Comment
from src.api.dependencies import (
    get_account_service,
    get_listing_service,
    get_comment_service,
)

router = APIRouter(prefix="/listings")
security = HTTPBearer()


def _listing_uploads_dir() -> Path:
    # server/uploads/listings
    path = Path(__file__).resolve().parents[3] / "uploads" / "listings"
    path.mkdir(parents=True, exist_ok=True)
    return path


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


# TODO: please change this
def _save_uploaded_image(upload: UploadFile, request: Request) -> str:
    if not (upload.content_type or "").startswith("image/"):
        raise ValueError("Uploaded file must be an image.")

    ext = _normalized_image_extension(upload)
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = _listing_uploads_dir() / filename

    with filepath.open("wb") as out_file:
        shutil.copyfileobj(upload.file, out_file)

    return f"/uploads/listings/{filename}"


@router.get("", response_model=List[ListingResponse])
def get_all_listing(
    _: int = Depends(get_current_user_id),
    listing_service: ListingService = Depends(get_listing_service),
):
    """Get all listings

    Args:
        _ (int, optional): Jwt auth token. Defaults to Depends(get_current_user_id).

    Returns:
        _type_: list of ListingResponse
    """
    listings: List[Listing] = listing_service.get_all_listing()

    return [ListingResponse.from_domain(listing) for listing in listings]


@router.get("/me", response_model=List[ListingResponse])
def get_my_listing(
    user_id: int = Depends(get_current_user_id),
    listing_service: ListingService = Depends(get_listing_service),
):
    """Get current user listings

    Args:
        _ (int, optional): Jwt auth token. Defaults to Depends(get_current_user_id).

    Returns:
        _type_:  list of ListingResponse
    """
    listings: List[Listing] = listing_service.get_listing_by_user_id(user_id=user_id)

    return [ListingResponse.from_domain(listing) for listing in listings]


@router.post("", response_model=ListingResponse)
def create_listing(
    request: ListingCreate,
    user_id: int = Depends(get_current_user_id),
    listing_service: ListingService = Depends(get_listing_service),
):
    """Creates a new listing.

    Args:
        request (ListingCreate): The listing creation request data.

    Returns:
        ListingResponse: The response model for the newly created listing.
    """
    listing: Listing = listing_service.create_listing(
        seller_id=user_id,
        title=request.title,
        description=request.description,
        price=request.price,
        location=request.location,
        image_url=request.image_url,
    )

    return ListingResponse.from_domain(listing)


@router.post("/upload", response_model=ListingResponse)
async def create_listing_with_upload(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    location: str = Form(...),
    image: UploadFile | None = File(default=None),
    user_id: int = Depends(get_current_user_id),
    listing_service: ListingService = Depends(get_listing_service),
):
    """Creates a listing using multipart/form-data and stores the uploaded image locally."""
    image_url = None
    if image is not None:
        try:
            image_url = _save_uploaded_image(image, request)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            ) from exc
        finally:
            await image.close()

    listing: Listing = listing_service.create_listing(
        seller_id=user_id,
        title=title,
        description=description,
        price=price,
        location=location,
        image_url=image_url,
    )

    return ListingResponse.from_domain(listing)


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(
    listing_id: int,
    user_id: int = Depends(get_current_user_id),
    listing_service: ListingService = Depends(get_listing_service),
):
    """Deletes a listing owned by the current user."""
    listing_service.delete_listing(listing_id=listing_id, actor_user_id=user_id)
    return None


# ============= Comments of a listing related calls ============= #
@router.get("/{listing_id}/comments", response_model=List[CommentResponse])
def get_listing_comment(
    listing_id: int,
    user_id: int = Depends(get_current_user_id),
    comment_service: CommentService = Depends(get_comment_service),
):
    """Get listing comments

    Args:
        listing_id (int): listing id
        user_id (int, optional): user id. Defaults to Depends(get_current_user_id).
        comment_service (CommentService, optional): DI for comment service. Defaults to Depends(get_comment_service).
    """
    comments: List[Comment] = comment_service.get_all_comments_listing(
        listing_id=listing_id
    )

    return [CommentResponse.from_domain(comment=comment) for comment in comments]


@router.post("/{listing_id}/comments", response_model=CommentResponse)
def create_listing_comment(
    listing_id: int,
    comment_request: CommentCreate,
    user_id: int = Depends(get_current_user_id),
    comment_service: CommentService = Depends(get_comment_service),
):
    """create a new listing

    Args:
        listing_id (int): listing id
        comment_request (CommentCreate): request body for comment
        user_id (int, optional): user id. Defaults to Depends(get_current_user_id).
        comment_service (CommentService, optional): Defaults to Depends(get_comment_service).
    """
    comment_request: Comment = comment_request.to_domain(
        listing_id=listing_id, author_id=user_id
    )
    comment_result: Comment = comment_service.create_comment(
        actor_id=user_id, listing_id=listing_id, comment=comment_request
    )

    return CommentResponse.from_domain(comment=comment_result)
