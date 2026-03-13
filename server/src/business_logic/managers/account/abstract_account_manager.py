from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, List

from src.db.account import AccountDB
from src.db.listing import ListingDB
from src.db.rating import BaseRatingDB
from src.domain_models import Account
from src.utils import Validation


class IAccountManager(ABC):
    """
    Account business layer contract (manager/service).

    Responsibilities:
        - Contains business logic and orchestration.
        - Calls persistence layer (AccountDB / ListingDB / BaseRatingDB) to read/write data.
        - Decides which domain errors to raise (404/409/422/etc.).
        - Does NOT write SQL.

    Dependency contract:
        - account_db: AccountDB (required)
        - listing_db: ListingDB (optional, used by listing orchestration methods)
        - rating_db: BaseRatingDB (optional, used by rating aggregate enrichment methods)
    """

    def __init__(
            self,
            account_db: AccountDB,
            listing_db: Optional[ListingDB] = None,
            rating_db: Optional[BaseRatingDB] = None,
    ) -> None:
        Validation.require_not_none(account_db, "account_db")
        self._account_db = account_db

        # Optional dependency (used only by specific methods)
        self._listing_db = listing_db

        # Optional dependency (used only for rating-related operations)
        self._rating_db = rating_db

    @abstractmethod
    def create_account(self, account: Account) -> Account:
        """
        PURPOSE:
            Create a new account.

        EXPECTED BEHAVIOR:
            - Accept an Account object (should already be structurally valid).
            - Enforce business rules required for creation.
            - Ensure email uniqueness:
                - If an account with the same email exists -> raise AccountAlreadyExistsError.
                - If two requests race, DB unique constraint may still raise; manager should
                  surface this as AccountAlreadyExistsError.
            - Persist the account through AccountDB.
            - Return the created Account with the generated database ID set.

        RETURNS:
            Account:
                The newly created account including its generated ID.

        RAISES (typical):
            - AccountAlreadyExistsError: email already taken.
            - ValidationError: if required fields are missing/invalid.
            - DatabaseUnavailableError / DatabaseQueryError: on infrastructure failures.
        """
        raise NotImplementedError

    @abstractmethod
    def get_account_by_id(self, account_id: int) -> Optional[Account]:
        """
        PURPOSE:
            Fetch an account by its database ID.

        EXPECTED BEHAVIOR:
            - Return the Account if it exists.
            - Return None if no account exists for this ID.
            - Must NOT raise an error just because it's not found.
              (Not found is a normal outcome for read operations.)
            - If rating_db is available, implementation may also populate:
                - average_rating_received
                - sum_of_ratings_received

        RETURNS:
            Account | None

        RAISES (typical):
            - ValidationError: if account_id is invalid
            - DatabaseUnavailableError / DatabaseQueryError: on infrastructure failures.
        """
        raise NotImplementedError

    @abstractmethod
    def get_account_by_email(self, email: str) -> Optional[Account]:
        """
        PURPOSE:
            Fetch an account by its unique email.

        EXPECTED BEHAVIOR:
            - Normalize/validate the email if needed (e.g., trim/lowercase).
            - Return the Account if it exists.
            - Return None if no account exists for this email.
            - Must NOT raise an error just because it's not found.
            - If rating_db is available, implementation may also populate:
                - average_rating_received
                - sum_of_ratings_received

        RETURNS:
            Account | None

        RAISES (typical):
            - ValidationError: if the email format is invalid.
            - DatabaseUnavailableError / DatabaseQueryError: on infrastructure failures.
        """
        raise NotImplementedError

    @abstractmethod
    def list_accounts(self) -> List[Account]:
        """
        PURPOSE:
            List all accounts.

        EXPECTED BEHAVIOR:
            - Return a list of all accounts.
            - If there are no accounts, return an empty list.
            - Never return None.
            - If rating_db is available, implementation may also populate:
                - average_rating_received
                - sum_of_ratings_received
              for each returned Account.

        RETURNS:
            list[Account]

        RAISES (typical):
            - DatabaseUnavailableError / DatabaseQueryError: on infrastructure failures.
        """
        raise NotImplementedError

    @abstractmethod
    def set_verified(self, account_id: int, verified: bool) -> None:
        """
        PURPOSE:
            Mark an account as verified/unverified.

        EXPECTED BEHAVIOR:
            - Update the verified flag for the given account ID.
            - This operation requires existence:
                - If account_id does not exist -> raise AccountNotFoundError.
            - Should not silently succeed when the account is missing.

        RETURNS:
            None

        RAISES (typical):
            - AccountNotFoundError: account_id does not exist.
            - ValidationError: if inputs are invalid.
            - DatabaseUnavailableError / DatabaseQueryError: on infrastructure failures.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_account(self, account_id: int) -> bool:
        """
        PURPOSE:
            Delete an account.

        EXPECTED BEHAVIOR:
            - Attempt to delete account row by ID.
            - Return True if a row was deleted.
            - Return False if no account matched the ID.
            - Must NOT raise AccountNotFoundError for missing row (delete is idempotent).

        RETURNS:
            bool:
                True if deleted, False if not found.

        RAISES (typical):
            - ValidationError: if account_id invalid (if manager validates).
            - DatabaseUnavailableError / DatabaseQueryError: on infrastructure failures.
        """
        raise NotImplementedError

    @abstractmethod
    def set_verified_by_email(self, email: str, verified: bool) -> None:
        """
        PURPOSE:
            Update a verified status using unique email.

        EXPECTED BEHAVIOR:
            - Normalize/validate email.
            - If the account with a given email does not exist -> raise AccountNotFoundError.
            - Update the verified flag.
            - Must not silently succeed if the account is missing.

        RETURNS:
            None

        RAISES:
            - AccountNotFoundError
            - ValidationError (if email invalid)
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def get_account_with_listings(self, account_id: int) -> Optional[Account]:
        """
        PURPOSE:
            Fetch an account and all listings posted by that account.

        EXPECTED BEHAVIOR:
            - Validate account_id.
            - If account does not exist -> return None.
            - Fetch listings using ListingDB.get_by_seller_id.
            - Attach listings to the Account domain object.
            - Return the composed Account.
            - Must NOT raise if account is missing (normal read outcome).
            - If rating_db is available, implementation may also populate:
                - average_rating_received
                - sum_of_ratings_received

        RETURNS:
            Account | None

        RAISES:
            - ValidationError
            - ConfigurationError (if ListingDB not provided)
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def get_account_with_listings_by_email(self, email: str) -> Optional[Account]:
        """
        PURPOSE:
            Fetch an account by email and populate its listings.

        EXPECTED BEHAVIOR:
            - Normalize/validate email.
            - If account does not exist -> return None.
            - Delegate to get_account_with_listings(account.id).
            - If rating_db is available, implementation may also populate:
                - average_rating_received
                - sum_of_ratings_received

        RETURNS:
            Account | None

        RAISES:
            - ValidationError
            - ConfigurationError (if ListingDB not provided)
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def get_account_with_listings_for(self, account: Account) -> Optional[Account]:
        """
        PURPOSE:
            Populate listings for a provided Account instance.

        EXPECTED BEHAVIOR:
            - Validate account object.
            - If account is not persisted (id is None) -> return None.
            - Delegate to get_account_with_listings(account.id).
            - If rating_db is available, implementation may also populate:
                - average_rating_received
                - sum_of_ratings_received

        RETURNS:
            Account | None

        RAISES:
            - ValidationError
            - ConfigurationError (if ListingDB not provided)
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def fill_account_rating_values(self, account: Account) -> Account:
        """
        PURPOSE:
            Populate rating aggregate values on an existing Account instance.

        EXPECTED BEHAVIOR:
            - Validate the account object.
            - If account is not persisted (id is None), return it unchanged.
            - Populate:
                - average_rating_received
                - sum_of_ratings_received
              using BaseRatingDB.
            - Return the same Account instance after enrichment.

        RETURNS:
            Account

        RAISES:
            - ValidationError
            - ConfigurationError (if BaseRatingDB not provided)
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def get_account_with_rating_values_by_id(self, account_id: int) -> Optional[Account]:
        """
        PURPOSE:
            Fetch an account by ID and populate rating aggregate values.

        EXPECTED BEHAVIOR:
            - Validate account_id.
            - If account does not exist -> return None.
            - Populate:
                - average_rating_received
                - sum_of_ratings_received
              using BaseRatingDB.

        RETURNS:
            Account | None

        RAISES:
            - ValidationError
            - ConfigurationError (if BaseRatingDB not provided)
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def get_account_with_rating_values_by_email(self, email: str) -> Optional[Account]:
        """
        PURPOSE:
            Fetch an account by email and populate rating aggregate values.

        EXPECTED BEHAVIOR:
            - Normalize/validate email.
            - If account does not exist -> return None.
            - Populate:
                - average_rating_received
                - sum_of_ratings_received
              using BaseRatingDB.

        RETURNS:
            Account | None

        RAISES:
            - ValidationError
            - ConfigurationError (if BaseRatingDB not provided)
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError
