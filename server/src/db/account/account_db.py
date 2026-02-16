# src/persistence/account_db.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, List

from src.db import DBUtility
from src.domain_models import Account


class AccountDB(ABC):
    """
    Contract for Account table persistence.

    IMPORTANT DESIGN RULES:

    - This layer is responsible ONLY for database access.
    - It does NOT contain business logic.
    - It does NOT decide HTTP responses.
    - It does NOT decide authentication logic.
    - It only performs CRUD operations.

    Methods that query data return Optional[Account]
    because "not found" is a valid database state.
    """

    def __init__(self, db: DBUtility) -> None:
        """
        The DBUtility instance must be injected.
        This allows:
        - Connection pooling reuse
        - Easier testing (mock DBUtility)
        - Clear separation of concerns
        """
        self._db = db

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------

    @abstractmethod
    def add(self, account: Account) -> Account:
        """
        Insert a new account row.

        Expected behavior:
        - Must insert the account into the database.
        - Must return the created Account with the generated ID.
        - Must raise an exception if:
            - Email already exists (unique constraint violation)
            - Database is unavailable
            - Any SQL error occurs

        Never returns None.
        """
        raise NotImplementedError

    # --------------------------------------------------
    # READ
    # --------------------------------------------------

    @abstractmethod
    def get_by_id(self, account_id: int) -> Optional[Account]:
        """
        Fetch account by primary key.

        Expected behavior:
        - Return Account if a row exists.
        - Return None if no row is found.
        - Must NOT raise exception for "not found".
        - Must raise exception if a database error occurs.
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[Account]:
        """
        Fetch account by unique email.

        Expected behavior:
        - Return Account if email exists.
        - Return None if no matching row exists.
        - Must NOT raise exception for "not found".
        - Must raise exception for database errors.
        """
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[Account]:
        """
        Fetch all accounts.

        Expected behavior:
        - Return an empty list if the table is empty.
        - Never return None.
        - Must raise an exception if a database error occurs.
        """
        raise NotImplementedError

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    @abstractmethod
    def set_verified(self, account_id: int, verified: bool) -> None:
        """
        Update the verified flag.

        Expected behavior:
        - Update the verified column for given ID.
        - If ID does not exist:
               raise a NotFound-style exception
          (Choose one and document it consistently.)
        - Must raise an exception if a database error occurs.
        """
        raise NotImplementedError

    @abstractmethod
    def set_verified_by_email(self, email: str, verified: bool) -> None:
        """
        Update verified by unique email.

        Behavior:
          - MUST raise AccountNotFoundError if email does not exist.
        """
        raise NotImplementedError

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------

    @abstractmethod
    def remove(self, account_id: int) -> bool:
        """
        Delete an account by ID.

        Expected behavior:
        - Return True if a row was deleted.
        - Return False if no row matched the ID.
        - Must NOT raise exception for "not found".
        - Must raise exception for database errors.
        """
        raise NotImplementedError

    # --------------------------------------------------
    # TEST / DEV
    # --------------------------------------------------

    @abstractmethod
    def clear_db(self) -> None:
        """
        Delete all rows from the account table.

        Expected behavior:
        - Remove all rows.
        - Used only for testing or development.
        - Must raise an exception if a database error occurs.
        """
        raise NotImplementedError