from fastapi import APIRouter, Depends
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from typing import List
from src.auth.dependencies import get_current_user_id
from src.business_logic.managers.account.account_manager import AccountManager
from src.db.account.mysql.mysql_account_db import MySQLAccountDB
from src.db.db_utils import DBUtility
from src.db.email_verification_token.mysql.mysql_email_verification_token_db import (
    MySQLEmailVerificationTokenDB,
)
from src.domain_models import Listing
from src.api.converter.listing_converter import ListingCreate, ListingResponse
from src.business_logic.services.listing_service import ListingService

router = APIRouter(prefix="/listings")
security = HTTPBearer()


def _get_service() -> ListingService:
    db = DBUtility.instance()
    account_db = MySQLAccountDB(db=db)
    # listing_manager = ListingManager(account_db=account_db)
    listing_manager = None  # placeholder until we implement the manager
    return ListingService(listing_manager=listing_manager)


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

    return [
        ListingResponse(
            title=listing.title,
            description=listing.description,
            price=listing.price,
            image_url=listing.image_url,
            location=listing.location,
            created_at=listing.created_at.isoformat() if listing.created_at else None,
            is_sold=listing.is_sold,
        )
        for listing in listings
    ]


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

    return [
        ListingResponse(
            title=listing.title,
            description=listing.description,
            price=listing.price,
            image_url=listing.image_url,
            location=listing.location,
            created_at=listing.created_at.isoformat() if listing.created_at else None,
            is_sold=listing.is_sold,
        )
        for listing in listings
    ]


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

    return ListingResponse(
        title=listing.title,
        description=listing.description,
        price=listing.price,
        image_url=listing.image_url,
        location=listing.location,
        created_at=listing.created_at.isoformat() if listing.created_at else None,
        is_sold=listing.is_sold,
    )
