from src.domain_models.account import Account
from src.api.errors.api_error import ApiError


class AccountService:
    def __init__(self):
        # will have a DAO instance here
        ...

    def create_account(
        self, email: str, password: str, fname: str, lname: str
    ) -> Account:
        # should call DAO create account here

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

    def get_account_by_userid(self, userid: str) -> Account:
        # should call DAO get account here

        acc_test: Account = Account(
            email="test1@gmail.com",
            password="test",
            fname="test",
            lname="test",
            account_id=1,
            verified=False,
        )
        # do logic here (error input checking etc, if any)
        ##

        ##
        return acc_test
