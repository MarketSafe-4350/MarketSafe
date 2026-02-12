from src.domain_models.account import Account
from src.api.errors.api_error import ApiError


class AccountService:
    def __init__(self): ...

    def create_account(
        self, email: str, password: str, fname: str, lname: str
    ) -> Account:

        # do logic here
        ##

        ## convert into account domain model
        account: Account = Account(
            email=email,
            password=password,
            fname=fname,
            lname=lname,
        )

        return account
