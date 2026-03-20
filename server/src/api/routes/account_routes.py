from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import logging

from src.api.dependencies import get_account_service
from src.auth.dependencies import get_current_user_id
from src.api.converter.account_converter import LoginRequest
from src.config import FRONTEND_URL
from src.api.converter import (
    AccountResponse,
    AccountSignup,
    Token,
    SignupResponse,
    VerifyEmailResponse,
)
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


@router.post("", response_model=SignupResponse)
def create_account(
    request: AccountSignup,
    account_service: AccountService = Depends(get_account_service),
):
    """Creates a new account and returns verification link.

    Args:
        request (AccountSignup): The account signup request data.

    Returns:
        SignupResponse: The response with account data and verification link.
    """
    try:
        account: Account = account_service.create_account(
            email=request.email,
            password=request.password,
            fname=request.fname,
            lname=request.lname,
        )

        # Generate verification auth_token and create link
        # NOTE: In production, this would be done after saving to DB
        # For now, using a mock account_id for demonstration
        raw_token = account_service.generate_and_store_verification_token(account_id=1)

        # Create verification link
        verification_link = f"{FRONTEND_URL}/verify-email?auth_token={raw_token}"

        logger.info(f"Account created for {account.email}")
        logger.info(f"Verification link: {verification_link}")

        return SignupResponse(
            email=account.email,
            fname=account.fname,
            lname=account.lname,
            verification_link=verification_link,
        )

    except Exception as e:
        logger.error(f"Failed to create account: {e}")
        return JSONResponse(status_code=500, content={"error_message": str(e)})


@router.post("/login", response_model=Token)
def login_account(
    request: LoginRequest,
    account_service: AccountService = Depends(get_account_service),
):
    """
    Authenticates a user and returns a JWT auth_token.

    Args:
        form_data (OAuth2PasswordRequestForm): The user login credentials (username and password).

    Returns:
        dict: A JSON object containing the access auth_token and auth_token type.
    """
    token = account_service.login(request.email, request.password)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=AccountResponse)
def get_account(
    user_id: int = Depends(get_current_user_id),
    account_service: AccountService = Depends(get_account_service),
):
    account = account_service.get_account_userid(user_id)

    return AccountResponse(
        email=account.email,
        fname=account.fname,
        lname=account.lname,
    )


@router.get("/verify-email", response_model=VerifyEmailResponse)
def verify_email(
    auth_token: str | None = Query(None, min_length=10),
    token: str | None = Query(None, min_length=10),
    account_service: AccountService = Depends(get_account_service),
):
    """
    Email verification endpoint: /accounts/verify-email?auth_token=...
    Supports legacy token query parameter for backwards compatibility.
    """
    try:
        verification_token = auth_token or token
        if not verification_token:
            return JSONResponse(
                status_code=400,
                content={"error_message": "No verification auth_token provided."},
            )

        account = account_service.verify_email_token(verification_token)

        logger.info(f"Email verified for account {account.email}")

        return VerifyEmailResponse(
            email=account.email,
            fname=account.fname,
            lname=account.lname,
            verified=account.verified,
            message="Email verified successfully!",
        )

    except (
        TokenNotFoundError,
        TokenExpiredError,
        TokenAlreadyUsedError,
        EmailVerificationError,
    ) as e:
        logger.warning(f"Email verification failed: {e.message}")
        return JSONResponse(
            status_code=e.status_code, content={"error_message": e.message}
        )
    except Exception as e:
        logger.error(f"Unexpected error during email verification: {e}")
        return JSONResponse(
            status_code=500,
            content={"error_message": "An error occurred during verification"},
        )
