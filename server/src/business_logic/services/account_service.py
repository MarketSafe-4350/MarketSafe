import jwt
import datetime

from src.business_logic.managers.account.account_manager import AccountManager
from src import SECRET_KEY
from src.api.errors import ApiError
from src.domain_models import Account
from src.utils.validation import Validation
from src.utils.errors import ValidationError, DatabaseUnavailableError, AccountAlreadyExistsError, AppError
from src.config import SECRET_KEY

import jwt
import datetime
import re


PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[^\s]{8,}$"
ALLOWED_DOMAINS = ("umanitoba.ca", "myumanitoba.ca")

class AccountService:
    """Service class for handling account-related business logic."""

    def __init__(self, account_manager: AccountManager):
        self.account_manager = account_manager

    def create_account(self, email: str, password: str, fname: str, lname: str) -> Account:
        """Creates a new account with the provided details.
           Validates provided details before creating account.

        Args:
            email (str): The email address for the new account.
            password (str): The password for the new account.
            fname (str): The first name of the account holder.
            lname (str): The last name of the account holder.

        Returns:
            Account: The newly created account domain model.
        """
        email, password, fname, lname = self.validate_account(email, password, fname, lname)
        account = Account(email=email, password=password, fname=fname, lname=lname)
    
        try:
            created = self.account_manager.create_account(account)
        except AccountAlreadyExistsError as e:
            raise AccountAlreadyExistsError(status_code=409, message=str(e))

        except ValidationError as e:
            raise ApiError(status_code=422, message=str(e))

        except DatabaseUnavailableError as e:
            raise ApiError(status_code=503, message=str(e))

        except Exception:
            raise ApiError(status_code=500, message="Internal server error")


        return created if created is not None else account


    def validate_account(self, email: str, password: str, fname: str, lname: str):
        """ Validates created account information

        Args: 
            email (str): The email address for the new account - passed from create_account.
            password (str): The password for the new account - passed from create_account.
            fname (str): The first name of the account holder - passed from create_account.
            lname (str): The last name of the account holder - passed from create_account.
        
        Returns:
            email, password, fname, lname - All validated from utils/validation.py and self methods

        Raises:
            ValidationError: If any input fails validation checks.
        """
        email = Validation.valid_email(email)
        self.validate_email(email)
        
        fname = Validation.require_str(fname, "First name")
        lname = Validation.require_str(lname, "Last name")

        Validation.not_empty(password, "Password")
        self.validate_password(password)

        return email, password, fname, lname
    
    def validate_email(self, email: str):
        domain = email.split("@")[-1]
        if domain not in ALLOWED_DOMAINS:
            raise ValidationError("Email must be a valid University of Manitoba email address "
                                    "(@umanitoba.ca / @myumanitoba.ca)")

    def validate_password(self, password: str):
        if not re.fullmatch(PASSWORD_REGEX, password):
            raise ValidationError(
                "Password must be at least 8 characters long and include "
                "1 uppercase, 1 lowercase, 1 number, and no spaces."
            )

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