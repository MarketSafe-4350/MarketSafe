from fastapi import APIRouter

from src.api.converter.account_converter import AccountSignup, AccountResponse
from src.business_logic.services.account_service import AccountService
from src.domain_models.account import Account

router = APIRouter(prefix="/accounts")
service = AccountService()


@router.post("", response_model=AccountResponse)
def create_account(request: AccountSignup):
    account: Account = service.create_account(
        email=request.email,
        password=request.password,
        fname=request.fname,
        lname=request.lname,
    )

    return AccountResponse(
        email=account.email, fname=account.fname, lname=account.lname
    )


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: str):
    account: Account = service.get_account_by_userid(account_id)

    return AccountResponse(
        email=account.email, fname=account.fname, lname=account.lname
    )
