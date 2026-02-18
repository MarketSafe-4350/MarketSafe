import jwt
import logging
import datetime

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


logger = logging.getLogger(__name__)


class AccountService:
    """Service class for handling account-related business logic."""

    def __init__(
        self,
        token_db: MySQLEmailVerificationTokenDB = None,
    ):
        """
        Initialize AccountService.

        Args:
            token_db: Database layer for email verification tokens
        """
        # Token database - will be injected or created if needed
        self.token_db = token_db

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
                message="Token cannot be empty",
                details={"token": token}
            )

        # Hash the provided token to look it up
        token_hash = TokenGenerator.hash_token(token)

        # Try to find the token in database
        db_token = self.token_db.get_by_hash(token_hash)

        if db_token is None:
            raise TokenNotFoundError(
                message="Invalid or expired verification token",
                details={"token_hash": token_hash}
            )

        # Check if token has been used already
        if db_token.used:
            raise TokenAlreadyUsedError(
                message="This verification token has already been used",
                details={"token_id": db_token.id}
            )

        # Check if token has expired
        if db_token.is_expired():
            raise TokenExpiredError(
                message="This verification token has expired",
                details={"token_id": db_token.id, "expires_at": str(db_token.expires_at)}
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
