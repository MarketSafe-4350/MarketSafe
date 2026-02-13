from server.src.api.errors import ApiError
from server.src.domain_models import Account
from server.src.utils import Validation
from server.src.utils.errors import ValidationError
import re

PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[^\s]{8,}$"
ALLOWED_DOMAINS = ("umanitoba.ca", "myumanitoba.ca")

class AccountService:
    """Service class for handling account-related business logic."""

    def __init__(self):
        # will have a DAO instance here
        ...

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
        email, password, fname, lname = self.validate_account(email, password, fname, lname)

        # should call DAO create account here

        ## convert into account domain model
        account: Account = Account(
            email=email,
            password=password,
            fname=fname,
            lname=lname,
        )

        return account

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
                                    "(@umanitoba.ca / @myumanitoba.ca")

    def validate_password(self, password: str):
        if not re.fullmatch(PASSWORD_REGEX, password):
            raise ValidationError(
                "Password must be at least 8 characters long and include "
                "1 uppercase, 1 lowercase, 1 number, and no spaces."
            )

    def get_account_by_userid(self, userid: str) -> Account:
        """Retrieves an account by its user ID.

        Args:
            userid (str): The unique identifier of the account to retrieve.

        Returns:
            Account: The retrieved account domain model.
        """
        # do logic here (this is an example)
        ##
        if userid is None:
            raise ApiError(status_code=400, message="userid cannot be None")

        # should call DAO get account here

        acc_test: Account = Account(
            email="test1@gmail.com",
            password="test",
            fname="test",
            lname="test",
            account_id=1,
            verified=False,
        )

        ##
        return acc_test
