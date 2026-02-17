import jwt
import datetime

from src.business_logic.managers.account.account_manager import AccountManager
from src import SECRET_KEY
from src.api.errors import ApiError
from src.domain_models import Account


class AccountService:
    """Service class for handling account-related business logic."""

    def __init__(self, account_manager: AccountManager):
        self.account_manager = account_manager

    def create_account(
            self, email: str, password: str, fname: str, lname: str
    ) -> Account:
        """Creates a new account with the provided details.

        Args:
            email (str): The email address for the new account.
            password (str): The password for the new account.
            fname (str): The first name of the account holder.
            lname (str): The last name of the account holder.

        Returns:
            Account: The newly created account domain model.
        """
        # do logic here
        ##

        # should call DAO create account here

        ## convert into account domain model
        account: Account = Account(
            email=email,
            password=password,
            fname=fname,
            lname=lname,
        )

        return account

    def get_account_by_email(self, email: str) -> Account:
        """Retrieves an account by its user ID.

        Args:
            userid (str): The unique identifier of the account to retrieve.

        Returns:
            Account: The retrieved account domain model.
        """
        if not email:
            raise ApiError(status_code=400, message="email is required")

        account = self.account_manager.get_account_by_email(email)

        if account is None:
            raise ApiError(status_code=404, message="Account not found")

        return account


    def login(self, email: str, password: str) -> str:

        """Authenticates a user and returns a JWT token.

        Args:
            email (str): The email of the user.
            password (str): The password of the user.

        Returns:
            str: A JWT token for the authenticated user.
        """

        if not email or not password:
            raise ApiError(status_code=400, message="Email and password are required")

        account = self.account_manager.get_account_by_email(email)

        if account is None:
            raise ApiError(status_code=401, message="Invalid email or password")

        if account.password != password:
            raise ApiError(status_code=401, message="Invalid email or password")
        
        #for when we implement password hashing
        ## if not bcrypt.checkpw(password.encode(), account.password.encode()):
        #raise ApiError(status_code=401, message="Invalid email or password")

        expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)

        token = jwt.encode(
            {
                "sub": account.email,
                "exp": expiration
            },
            SECRET_KEY,
            algorithm="HS256"
        )

        return token