import jwt
import logging
import datetime
import re

from src.business_logic.managers.account.account_manager import AccountManager
from src import SECRET_KEY
from src.api.errors import ApiError
from src.domain_models import Account, VerificationToken
from src.db.email_verification_token.mysql import MySQLEmailVerificationTokenDB
from src.utils import (
    TokenGenerator,
    TokenNotFoundError,
    TokenExpiredError,
    TokenAlreadyUsedError,
    EmailVerificationError,
)
from src.utils.validation import Validation
from src.utils.errors import (
    ValidationError,
    DatabaseUnavailableError,
    AccountAlreadyExistsError,
    AppError,
)
from src.config import SECRET_KEY


logger = logging.getLogger(__name__)


PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[^\s]{8,}$"
ALLOWED_DOMAINS = ("umanitoba.ca", "myumanitoba.ca")


class AccountService:
    """Service class for handling account-related business logic."""

    def __init__(
        self,
        account_manager: AccountManager = None,
        token_db: MySQLEmailVerificationTokenDB = None,
    ):
        """
        Initialize AccountService.

        Args:
            account_manager: Manager for account database operations (optional)
            token_db: Database layer for email verification tokens (optional)
        """
        self.account_manager = account_manager
        self.token_db = token_db

    def create_account(
        self, email: str, password: str, fname: str, lname: str
    ) -> Account:
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
        email, password, fname, lname = self.validate_account(
            email, password, fname, lname
        )
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
        """Validates created account information

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
            raise ValidationError(
                "Email must be a valid University of Manitoba email address "
                "(@umanitoba.ca / @myumanitoba.ca)"
            )

    def validate_password(self, password: str):
        if not re.fullmatch(PASSWORD_REGEX, password):
            raise ValidationError(
                "Password must be at least 8 characters long and include "
                "1 uppercase, 1 lowercase, 1 number, and no spaces."
            )

    def generate_and_store_verification_token(self, account_id: int) -> str:
        """
        Generate a verification token and store it in the database.

        This should be called immediately after creating a new account.

        Args:
            account_id (int): The ID of the account to generate token for

        Returns:
            str: The raw token (to be sent in email)

        Raises:
            DatabaseQueryError: If token storage fails
        """
        # Generate token pair: raw token, hash, and expiry
        raw_token, token_hash, expires_at = TokenGenerator.create_token_pair()

        # Create VerificationToken domain model
        verification_token = VerificationToken(
            account_id=account_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        # Store in database
        self.token_db.add(verification_token)

        logger.info(f"Generated verification token for account {account_id}")

        return raw_token

    def verify_email_token(self, token: str) -> Account:
        """
        Verify an email token and mark the account as verified.

        This is called when the user clicks the verification link.

        Args:
            token (str): The raw verification token from the email link

        Returns:
            Account: The verified account

        Raises:
            TokenNotFoundError: If token doesn't exist
            TokenExpiredError: If token has expired
            TokenAlreadyUsedError: If token was already used
            AccountNotFoundError: If account not found
        """
        if not token:
            raise EmailVerificationError(
                message="Token cannot be empty", details={"token": token}
            )

        # Hash the provided token to look it up
        token_hash = TokenGenerator.hash_token(token)

        # Try to find the token in database
        db_token = self.token_db.get_by_hash(token_hash)

        if db_token is None:
            raise TokenNotFoundError(
                message="Invalid or expired verification token",
                details={"token_hash": token_hash},
            )

        # Check if token has been used already
        if db_token.used:
            raise TokenAlreadyUsedError(
                message="This verification token has already been used",
                details={"token_id": db_token.id},
            )

        # Check if token has expired
        if db_token.is_expired():
            raise TokenExpiredError(
                message="This verification token has expired",
                details={
                    "token_id": db_token.id,
                    "expires_at": str(db_token.expires_at),
                },
            )

        # Get the account and mark as verified
        account = self.get_account_by_userid(db_token.account_id)

        # TODO: Call DAO to update account.verified = true
        # For now, we'll return the account (real implementation will update DB)
        account.verified = True

        # Mark token as used ONLY after successful verification
        self.token_db.mark_used(db_token.id)

        logger.info(f"Account {db_token.account_id} verified successfully")
        return account

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

    def get_account_by_email(self, email: str) -> Account:
        """Retrieves an account by email address.

        Args:
            email (str): The email address of the account to retrieve.

        Returns:
            Account: The retrieved account domain model.

        Raises:
            ApiError: If account not found.
        """
        if not email:
            raise ApiError(status_code=400, message="Email cannot be empty")

        account = self.account_manager.get_account_by_email(email)

        if account is None:
            raise ApiError(
                status_code=404, message=f"Account not found for email: {email}"
            )

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

        # Get account from database
        account = self.account_manager.get_account_by_email(email)

        if account is None:
            raise ApiError(status_code=401, message="Invalid email or password")

        if account.password != password:
            raise ApiError(status_code=401, message="Invalid email or password")

        # for when we implement password hashing
        ## if not bcrypt.checkpw(password.encode(), account.password.encode()):
        # raise ApiError(status_code=401, message="Invalid email or password")

        expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            days=30
        )

        token = jwt.encode(
            {"sub": str(account.id), "exp": expiration}, SECRET_KEY, algorithm="HS256"
        )
        return token

    def get_account_userid(self, userid: int) -> Account:
        if userid is None:
            raise ApiError(status_code=400, message="User ID cannot be None")

        account = self.account_manager.get_account_by_id(userid)

        if account is None:
            raise ApiError(status_code=404, message="Account not found")

        return account
