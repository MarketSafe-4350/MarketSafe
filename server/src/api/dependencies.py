from src.db.utils import DBUtility
from src.business_logic.services import ListingService, CommentService, AccountService, OfferService
from src.business_logic.managers.listing import ListingManager
from src.business_logic.managers.comment import CommentManager
from src.business_logic.managers.account import AccountManager
from src.business_logic.managers.offer import OfferManager
from src.db.email_verification_token.mysql import MySQLEmailVerificationTokenDB
from src.db.account.mysql import MySQLAccountDB
from src.db.listing.mysql import MySQLListingDB
from src.db.comment.mysql import MySQLCommentDB
from src.db.offer.mysql import MySQLOfferDB

from fastapi import Depends

def get_db() -> DBUtility:
    return DBUtility.instance()

# -----------------------------
# DB layer dependencies
# -----------------------------
def get_account_db(db: DBUtility = Depends(get_db)) -> MySQLAccountDB:
    return MySQLAccountDB(db=db)


def get_listing_db(db: DBUtility = Depends(get_db)) -> MySQLListingDB:
    return MySQLListingDB(db=db)


def get_comment_db(db: DBUtility = Depends(get_db)) -> MySQLCommentDB:
    return MySQLCommentDB(db=db)


def get_email_token_db(db: DBUtility = Depends(get_db)) -> MySQLEmailVerificationTokenDB:
    return MySQLEmailVerificationTokenDB(db=db)


def get_offer_db(db: DBUtility = Depends(get_db)) -> MySQLOfferDB:
    return MySQLOfferDB(db=db)

# -----------------------------
# Manager layer dependencies
# -----------------------------
def get_account_manager(
    account_db: MySQLAccountDB = Depends(get_account_db),
) -> AccountManager:
    return AccountManager(account_db=account_db)


def get_comment_manager(
    comment_db: MySQLCommentDB = Depends(get_comment_db),
) -> CommentManager:
    return CommentManager(comment_db=comment_db)


def get_listing_manager(
    listing_db: MySQLListingDB = Depends(get_listing_db),
    comment_db: MySQLCommentDB = Depends(get_comment_db),
) -> ListingManager:
    return ListingManager(listing_db=listing_db, comment_db=comment_db)

def get_offer_manager(
    offer_db: MySQLOfferDB = Depends(get_offer_db),
    listing_db: MySQLListingDB = Depends(get_listing_db),
) -> OfferManager:
    return OfferManager(offer_db=offer_db, listing_db=listing_db)

# -----------------------------
# Service layer dependencies
# -----------------------------
def get_account_service(
    account_manager: AccountManager = Depends(get_account_manager),
    token_db: MySQLEmailVerificationTokenDB = Depends(get_email_token_db),
) -> AccountService:
    return AccountService(account_manager=account_manager, token_db=token_db)


def get_comment_service(
    comment_manager: CommentManager = Depends(get_comment_manager),
    listing_manager: ListingManager = Depends(get_listing_manager),
    account_manager: AccountManager = Depends(get_account_manager),
) -> CommentService:
    return CommentService(comment_manager=comment_manager, 
                          listing_manager=listing_manager, 
                          account_manager=account_manager
                          )


def get_listing_service(
    listing_manager: ListingManager = Depends(get_listing_manager),
) -> ListingService:
    return ListingService(listing_manager=listing_manager)


def get_offer_service(
    offer_manager: OfferManager = Depends(get_offer_manager),
    listing_manager: ListingManager = Depends(get_listing_manager),
    account_manager: AccountManager = Depends(get_account_manager), 
) -> OfferService:
    return OfferService(offer_manager=offer_manager,
                        listing_manager=listing_manager, 
                        account_manager=account_manager
                        )