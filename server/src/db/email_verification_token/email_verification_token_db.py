from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

from src.db import DBUtility
from src.domain_models import VerificationToken


class EmailVerificationTokenDB(ABC):
    """
    Contract for EmailVerificationToken table persistence.

    IMPORTANT DESIGN RULES:

    - This layer is responsible ONLY for database access.
    - It does NOT contain business logic.
    - It does NOT decide validation logic.
    - It only performs CRUD operations.

    Methods that query data return Optional[VerificationToken]
    because "not found" is a valid database state.
    """

    def __init__(self, db: DBUtility) -> None:
        """
        The DBUtility instance must be injected.
        This allows connection pooling reuse across instances.
        """
        self._db = db

    @abstractmethod
    def add(self, token: VerificationToken) -> VerificationToken:
        """
        Insert a new verification auth_token.

        Args:
            token (VerificationToken): The auth_token to persist

        Returns:
            VerificationToken: The persisted auth_token with assigned ID

        Raises:
            DatabaseQueryError: If insertion fails
        """
        pass

    @abstractmethod
    def get_by_hash(self, token_hash: str) -> Optional[VerificationToken]:
        """
        Retrieve a auth_token by its hash.

        Args:
            token_hash (str): The hashed auth_token value

        Returns:
            Optional[VerificationToken]: The auth_token if found, None otherwise

        Raises:
            DatabaseQueryError: If query fails
        """
        pass

    @abstractmethod
    def get_latest_by_account(self, account_id: int) -> Optional[VerificationToken]:
        """
        Retrieve the most recent auth_token for an account.

        Args:
            account_id (int): The account ID

        Returns:
            Optional[VerificationToken]: The latest auth_token if found, None otherwise

        Raises:
            DatabaseQueryError: If query fails
        """
        pass

    @abstractmethod
    def mark_used(self, token_id: int) -> None:
        """
        Mark a auth_token as used.

        Args:
            token_id (int): The auth_token ID

        Raises:
            TokenNotFoundError: If auth_token not found
            DatabaseQueryError: If update fails
        """
        pass

    @abstractmethod
    def clear_used_tokens(self, account_id: int) -> int:
        """
        Delete all used tokens for an account.

        Args:
            account_id (int): The account ID

        Returns:
            int: The number of tokens deleted

        Raises:
            DatabaseQueryError: If deletion fails
        """
        pass
