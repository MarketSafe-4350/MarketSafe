from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt

from src import SECRET_KEY
from src.api.errors.api_error import ApiError
from src.api.converter import AccountResponse, AccountSignup, Token
from src.business_logic.services import AccountService
from src.domain_models import Account

router = APIRouter(prefix="/accounts")
# service = AccountService()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/accounts/login")


def get_account_service(request: Request) -> AccountService:
    return request.app.state.account_service

@router.post("", response_model=AccountResponse)
# def create_account(request: AccountSignup):
def create_account(request: AccountSignup, service: AccountService = Depends(get_account_service)):

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
def login_account(form_data: OAuth2PasswordRequestForm = Depends(), 
                  service: AccountService = Depends(get_account_service),):
    """
    Authenticates a user and returns a JWT token.

    Args:
        form_data (OAuth2PasswordRequestForm): The user login credentials (username and password).

    Returns:
        dict: A JSON object containing the access token and token type.
    """

    try:

        token = service.login(form_data.username, form_data.password)

        if not token:
            raise ApiError(status_code=401, detail="Authentication failed.")

        return {"access_token": token, "token_type": "bearer"}

    except ApiError as error:
        return JSONResponse(
            status_code=error.status_code,
            content={"error_message": error.message}
        )


@router.get("/me", response_model=AccountResponse)
# def get_account(token: str = Depends(oauth2_scheme)):
def get_account(
    token: str = Depends(oauth2_scheme),
    service: AccountService = Depends(get_account_service),
):
    ...

    """Retrieves the current user's information using the user_id from the JWT token.

    Args:
        token (str): The JWT token containing the user's identity.

    Returns:
        AccountResponse: The account details of the authenticated user.
    """

    try:

        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        account_id = payload.get("sub")

        if not account_id:
            raise ApiError(status_code=401, detail="Could not validate user.")

        account = service.get_account_by_userid(account_id)
        return AccountResponse(email=account.email, fname=account.fname, lname=account.lname)

    except jwt.ExpiredSignatureError:
        raise ApiError(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError:
        raise ApiError(status_code=401, detail="Invalid token.")
