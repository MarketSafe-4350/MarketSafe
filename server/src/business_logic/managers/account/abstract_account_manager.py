from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, List

from src.domain_models import Account


class IAccountManager(ABC):
    """
    Account business layer contract (manager/service).

    Responsibilities:
        - Contains business logic and orchestration.
        - Calls persistence layer (AccountDB) to read/write data.
        - Decides which domain errors to raise (404/409/422/etc.).
        - Does NOT write SQL.
    """

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
        Update a verified status using unique email.

        EXPECTED BEHAVIOR:
            - Normalize/validate email.
            - If the account with a given email does not exist -> raise AccountNotFoundError.
            - Update the verified flag.
            - Must not silently succeed if the account is missing.

        RAISES:
            - AccountNotFoundError
            - ValidationError (if email invalid)
        """
        raise NotImplementedError


    @abstractmethod
    def clear_accounts(self) -> None:
        """
        PURPOSE:
            Clear all rows from the `account` table.

        EXPECTED BEHAVIOR:
            - Calls the persistence layer (AccountDB.clear_db()) to delete all rows.
            - Intended ONLY for testing / development utilities.
            - Must raise if any database error occurs (do not swallow exceptions).
            - Should not be exposed in production API routes.

        RETURNS:
            None

        RAISES (typical):
            - DatabaseUnavailableError / DatabaseQueryError: on infrastructure failures.
        """
        raise NotImplementedError

