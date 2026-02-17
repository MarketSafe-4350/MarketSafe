from src.api.errors import ApiError
from src.domain_models import Account
from src.utils.validation import Validation
from src.utils.errors import ValidationError, DatabaseUnavailableError, AccountAlreadyExistsError, AppError
from src.config import SECRET_KEY
from src.business_logic.managers.account import AccountManager
# from src.business_logic.managers.account import IAccountManager

from src.db.account.mysql import MySQLAccountDB
from src.db import DBUtility

import jwt
import datetime
import re


PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[^\s]{8,}$"
ALLOWED_DOMAINS = ("umanitoba.ca", "myumanitoba.ca")

class AccountService:
    """Service class for handling account-related business logic."""

    # def __init__(self):
    # # def __init__(self, account_dao):
    # #     self.account_dao = account_dao
    #     ...

    # def create_account(
    #         self, email: str, password: str, fname: str, lname: str
    # ) -> Account:
    #     """Creates a new account with the provided details.
    #        Validates provided details before creating account.

    #     Args:
    #         email (str): The email address for the new account.
    #         password (str): The password for the new account.
    #         fname (str): The first name of the account holder.
    #         lname (str): The last name of the account holder.

    #     Returns:
    #         Account: The newly created account domain model.
    #     """
    #     email, password, fname, lname = self.validate_account(email, password, fname, lname)

    #     # should call DAO create account here
    #     # if self.account_dao._account_db.get_by_email(email) is not None:
    #     #     raise ValidationError("Email is already in use.")
    #     ## convert into account domain model
    #     account: Account = Account(
    #         email=email,
    #         password=password,
    #         fname=fname,
    #         lname=lname,
    #     )

    #     # call account_manager.create_account to add account to db
    #     try:
    #         AccountManager.create_account(account)
    #     catch:
    #         email exists error

    #     return account


class AccountService:
    def __init__(self, account_manager):
        self.account_manager = account_manager
    # def __init__(self, db=None):
    #     # db = DBUtility.instance()
    #     # account_db = MySQLAccountDB(db=db)
    #     # self.account_manager = AccountManager(account_db)
    #     self.account_manager = AccountManager(db)



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
            return self.account_manager.create_account(account)

        except (ValidationError, AccountAlreadyExistsError, DatabaseUnavailableError):
            # already has correct status_code + message
            raise

        except Exception:
            # unexpected bug
            raise AppError(message="Internal server error", status_code=500)
    
        # try:
        #     created = self.account_manager.create_account(account)
        # except AccountAlreadyExistsError as e:
        #     # service layer maps domain conflict to API response
        #     raise AccountAlreadyExistsError(status_code=409, message=str(e))

        # except ValidationError as e:
        #     raise ApiError(status_code=422, message=str(e))

        # except DatabaseUnavailableError as e:
        #     raise ApiError(status_code=503, message=str(e))

        # except Exception:
        #     raise ApiError(status_code=500, message="Internal server error")


        
        # except ValidationError as e:
        #     msg = str(e).lower()
        #     if "exists" in msg or "already" in msg or "duplicate" in msg:
        #         raise AccountAlreadyExistsError(status_code=409, message="Email is already in use")
        #     raise ApiError(status_code=400, message=str(e))
        # except DatabaseUnavailableError:
        #     raise ApiError(status_code=503, message="Database unavailable")
        # except Exception:
        #     raise ApiError(status_code=500, message="Internal server error")

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

        # mock data for test, set up db check
        if email == "test1@gmail.com" and password == "test":
            expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
            token = jwt.encode({
                "sub": "test1@gmail.com",
                "exp": expiration
            }, SECRET_KEY, algorithm="HS256")
            return token

        raise ApiError(status_code=401, message="Invalid email or password")
