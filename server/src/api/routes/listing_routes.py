import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from typing import List
from src.auth.dependencies import get_current_user_id
from src.business_logic.managers.listing.listing_manager import ListingManager
from src.db.listing.mysql.mysql_listing_db import MySQLListingDB
from src.business_logic.managers.listing.abstract_listing_manager import CommentDB
from src.business_logic.managers.account.account_manager import AccountManager
from src.db.account.mysql.mysql_account_db import MySQLAccountDB
from src.db.utils.db_utils import DBUtility
from src.db.email_verification_token.mysql.mysql_email_verification_token_db import (
    MySQLEmailVerificationTokenDB,
)
from src.domain_models import Listing
from src.api.converter.listing_converter import ListingCreate, ListingResponse
from src.business_logic.services.listing_service import ListingService
from src.domain_models.comment import Comment

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
    db = DBUtility.instance()
    listing_db = MySQLListingDB(db=db)
    # placeholder for now, will change when comment db is implemented
    comment_db = _NoOpCommentDB(db=db)
    listing_manager = ListingManager(listing_db=listing_db, comment_db=comment_db)
    return ListingService(listing_manager=listing_manager)


def _to_listing_response(listing: Listing) -> ListingResponse:
    return ListingResponse(
        id=listing.id,
        seller_id=listing.seller_id,
        title=listing.title,
        description=listing.description,
        price=listing.price,
        image_url=listing.image_url,
        location=listing.location,
        created_at=listing.created_at.isoformat() if listing.created_at else None,
        is_sold=listing.is_sold,
    )


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
def get_all_listing(_: int = Depends(get_current_user_id)):
    """Get all listings

    Args:
        _ (int, optional): Jwt auth token. Defaults to Depends(get_current_user_id).

    Returns:
        _type_: list of ListingResponse
    """
    service = _get_service()

    listings: List[Listing] = service.get_all_listing()

    return [_to_listing_response(listing) for listing in listings]


@router.get("/me", response_model=List[ListingResponse])
def get_my_listing(user_id: int = Depends(get_current_user_id)):
    """Get current user listings

    Args:
        _ (int, optional): Jwt auth token. Defaults to Depends(get_current_user_id).

    Returns:
        _type_:  list of ListingResponse
    """
    service = _get_service()

    listings: List[Listing] = service.get_listing_by_user_id(user_id=user_id)

    return [_to_listing_response(listing) for listing in listings]


@router.post("", response_model=ListingResponse)
def create_listing(
    request: ListingCreate,
    user_id: int = Depends(get_current_user_id),
):
    """Creates a new listing.

    Args:
        request (ListingCreate): The listing creation request data.

    Returns:
        ListingResponse: The response model for the newly created listing.
    """
    service = _get_service()

    listing: Listing = service.create_listing(
        seller_id=user_id,
        title=request.title,
        description=request.description,
        price=request.price,
        location=request.location,
        image_url=request.image_url,
    )

    return _to_listing_response(listing)


@router.post("/upload", response_model=ListingResponse)
async def create_listing_with_upload(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    location: str = Form(...),
    image: UploadFile | None = File(default=None),
    user_id: int = Depends(get_current_user_id),
):
    """Creates a listing using multipart/form-data and stores the uploaded image locally."""
    service = _get_service()

    image_url = None
    if image is not None:
        try:
            image_url = _save_uploaded_image(image, request)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        finally:
            await image.close()

    listing: Listing = service.create_listing(
        seller_id=user_id,
        title=title,
        description=description,
        price=price,
        location=location,
        image_url=image_url,
    )

    return _to_listing_response(listing)


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(
    listing_id: int,
    user_id: int = Depends(get_current_user_id),
):
    """Deletes a listing owned by the current user."""
    service = _get_service()

    service.delete_listing(listing_id=listing_id, actor_user_id=user_id)
    return None
