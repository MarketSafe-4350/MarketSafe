from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import logging

from src.business_logic.services import auth
from src.api.converter.account_converter import LoginRequest
from src.config import FRONTEND_URL
from src.api.converter import AccountResponse, AccountSignup, Token, SignupResponse, VerifyEmailResponse
from src.business_logic.services import AccountService
from src.business_logic.managers.account import AccountManager
from src.db.account.mysql import MySQLAccountDB
from src.db import DBUtility
from src.db.email_verification_token.mysql import MySQLEmailVerificationTokenDB
from src.domain_models import Account
from src.utils import (
    TokenNotFoundError,
    TokenExpiredError,
    TokenAlreadyUsedError,
    EmailVerificationError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/accounts")

security = HTTPBearer()

# Helper function to get service when needed


def _get_service() -> AccountService:
    db = DBUtility.instance()
    account_db = MySQLAccountDB(db=db)
    account_manager = AccountManager(account_db=account_db)
    token_db = MySQLEmailVerificationTokenDB(db=db)
    return AccountService(account_manager=account_manager, token_db=token_db)


@router.post("", response_model=SignupResponse)
def create_account(request: AccountSignup):
    """Creates a new account and returns verification link.

    Args:
        request (AccountSignup): The account signup request data.

    Returns:
        SignupResponse: The response with account data and verification link.
    """
    service = _get_service()
    try:
        account: Account = service.create_account(
            email=request.email,
            password=request.password,
            fname=request.fname,
            lname=request.lname,
        )

        # Generate verification token and create link
        # NOTE: In production, this would be done after saving to DB
        # For now, using a mock account_id for demonstration
        raw_token = service.generate_and_store_verification_token(account_id=1)

        # Create verification link
        verification_link = f"{FRONTEND_URL}/verify-email?token={raw_token}"

        logger.info(f"Account created for {account.email}")
        logger.info(f"Verification link: {verification_link}")

        return SignupResponse(
            email=account.email,
            fname=account.fname,
            lname=account.lname,
            verification_link=verification_link
        )

    except Exception as e:
        logger.error(f"Failed to create account: {e}")
        return JSONResponse(
            status_code=500,
            content={"error_message": str(e)}
        )


@router.post("/login", response_model=Token)
def login_account(request: LoginRequest):
    """
    Authenticates a user and returns a JWT token.

    Args:
        form_data (OAuth2PasswordRequestForm): The user login credentials (username and password).

    Returns:
        dict: A JSON object containing the access token and token type.
    """
    service = _get_service()
    
    token = service.login(request.email, request.password)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=AccountResponse)
def get_account(
     credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
    service = _get_service()
    
    token = credentials.credentials
    user_id = auth.auth_user(token)
    
    account = service.get_account_userid(user_id)

    return AccountResponse(
        email=account.email,
        fname=account.fname,
        lname=account.lname,
    )

@router.get("/verify-email", response_model=VerifyEmailResponse)
def verify_email(token: str = Query(..., min_length=10)):
    """
    Email verification endpoint: /accounts/verify-email?token=...
    Verifies the token and marks the user as verified.
    """
    service = _get_service()
    try:
        account = service.verify_email_token(token)

        logger.info(f"Email verified for account {account.email}")

        return VerifyEmailResponse(
            email=account.email,
            fname=account.fname,
            lname=account.lname,
            verified=account.verified,
            message="Email verified successfully!"
        )

    except (TokenNotFoundError, TokenExpiredError, TokenAlreadyUsedError, EmailVerificationError) as e:
        logger.warning(f"Email verification failed: {e.message}")
        return JSONResponse(
            status_code=e.status_code,
            content={"error_message": e.message}
        )
    except Exception as e:
        logger.error(f"Unexpected error during email verification: {e}")
        return JSONResponse(
            status_code=500,
            content={"error_message": "An error occurred during verification"}
        )


def create_account_router(service: AccountService):
    """
    We ignore the passed-in service for now because this module already uses _get_service().
    """
    return router

