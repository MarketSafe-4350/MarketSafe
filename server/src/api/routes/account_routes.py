from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt

from src import SECRET_KEY
from src.api.errors.api_error import ApiError
from src.api.converter import AccountResponse, AccountSignup, Token
from src.business_logic.services.account_service import AccountService
from src.domain_models import Account

def create_account_router(service: AccountService) -> APIRouter:
    router = APIRouter(prefix="/accounts")
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/accounts/login")


    @router.post("", response_model=AccountResponse)
    def create_account(request: AccountSignup):
        """Creates a new account.

        Args:
            request (AccountSignup): The account signup request data.

        Returns:
            AccountResponse: The response model for the newly created account.
        """
        account: Account = service.create_account(
            email=request.email,
            password=request.password,
            fname=request.fname,
            lname=request.lname,
        )

        return AccountResponse(
            email=account.email, fname=account.fname, lname=account.lname
        )


    @router.post("/login", response_model=Token)
    def login_account(form_data: OAuth2PasswordRequestForm = Depends()):
        """
        Authenticates a user and returns a JWT token.

        Args:
            form_data (OAuth2PasswordRequestForm): The user login credentials (username and password).

        Returns:
            dict: A JSON object containing the access token and token type.
        """

        token = service.login(form_data.username, form_data.password)
        return {"access_token": token, "token_type": "bearer"}


    @router.get("/me", response_model=AccountResponse)
    def get_account(token: str = Depends(oauth2_scheme)):
        """Retrieves the current user's information using the user_id from the JWT token.

        Args:
            token (str): The JWT token containing the user's identity.

        Returns:
            AccountResponse: The account details of the authenticated user.
        """

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            email = payload.get("sub")   # JWT subject now represents email

            if not email:
                raise ApiError(status_code=401, message="Could not validate user.")

            account = service.get_account_by_email(email)

            return AccountResponse(
                email=account.email,
                fname=account.fname,
                lname=account.lname
            )

        except jwt.ExpiredSignatureError:
            raise ApiError(status_code=401, message="Token has expired.")
        except jwt.InvalidTokenError:
            raise ApiError(status_code=401, message="Invalid token.")
        
    return router
