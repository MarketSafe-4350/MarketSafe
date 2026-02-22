from __future__ import annotations
from typing import Optional, List

from typing_extensions import override

from src.business_logic.managers.account import IAccountManager
from src.db.account import AccountDB
from src.db.listing import ListingDB
from src.domain_models import Account
from src.utils import Validation, AccountAlreadyExistsError, AccountNotFoundError, ConfigurationError


class AccountManager(IAccountManager):
    """
    Concrete business/service implementation.

    - Validates inputs
    - Enforces business rules (unique email, etc.)
    - Delegates SQL work to AccountDB
    """

    class AccountManager(IAccountManager):
        def __init__(self, account_db: AccountDB, listing_db: Optional[ListingDB] = None) -> None:
            super().__init__(account_db, listing_db)

    @override
    def create_account(self, account: Account) -> Account:
        Validation.require_not_none(account, "account")

        # Business rule: must not yet exist
        existing = self._account_db.get_by_email(account.email)
        if existing is not None:
            # You can either raise AccountAlreadyExistsError directly
            # or raise a generic ConflictError; you're already using AccountAlreadyExistsError
            raise AccountAlreadyExistsError(
                message=f"Account already exists for email: {account.email}",
                details={"email": account.email},
            )

        # Let persistence insert (it may also raise AccountAlreadyExistsError if race condition)
        return self._account_db.add(Account(
            account_id=None,
            email=account.email,
            password=account.password,
            fname=account.fname.strip(),
            lname=account.lname.strip(),
            verified=bool(account.verified),
        ))

    @override
    def get_account_by_id(self, account_id: int) -> Optional[Account]:
        Validation.require_int(account_id, "account_id")
        return self._account_db.get_by_id(account_id)

    @override
    def get_account_by_email(self, email: str) -> Optional[Account]:
        email = Validation.valid_email(email)
        return self._account_db.get_by_email(email)

    @override
    def list_accounts(self) -> List[Account]:
        return self._account_db.get_all()

    @override
    def set_verified(self, account_id: int, verified: bool) -> None:
        Validation.require_int(account_id, "account_id")
        Validation.is_boolean(verified, "verified")

        # Contract: persistence raises AccountNotFoundError if id missing
        self._account_db.set_verified(account_id, verified)

    @override
    def set_verified_by_email(self, email: str, verified: bool) -> None:
        email = Validation.valid_email(email)
        Validation.is_boolean(verified, "verified")
        self._account_db.set_verified_by_email(email, verified)

    @override
    def delete_account(self, account_id: int) -> bool:
        Validation.require_int(account_id, "account_id")
        return self._account_db.remove(account_id)

    def require_account_by_id(self, account_id: int) -> Account:
        acc = self.get_account_by_id(account_id)
        if acc is None:
            raise AccountNotFoundError(
                message=f"Account not found for id: {account_id}",
                details={"account_id": account_id},
            )
        return acc

    from typing import Optional

    @override
    def get_account_with_listings(self, account_id: int) -> Optional[Account]:
        """
        Orchestration:
          - account_db.get_by_id(account_id)
          - listing_db.get_by_seller_id(account_id)
          - attach listings to Account via account.add_listing(...)
          - return Account (or None if not found)

        Notes:
          - This method requires ListingDB to be provided (optional dependency).
          - We return the Account domain object with its internal listings populated.
        """
        account_id = Validation.require_int(account_id, "account_id")

        # Requires optional dependency
        if self._listing_db is None:
            raise ConfigurationError(
                message="ListingDB dependency is required for get_account_with_listings().",
                details={"missing_dependency": "ListingDB"},
            )

        account = self._account_db.get_by_id(account_id)
        if account is None:
            return None

        listings = self._listing_db.get_by_seller_id(account_id)

        # Attach safely through domain method (enforces seller_id invariant)
        for listing in listings:
            account.add_listing(listing)

        return account

    def get_account_with_listings_by_email(self, email: str) -> Optional[Account]:
        """
        Wrapper:
            - Normalize/validate email
            - Fetch account by email
            - Delegate to get_account_with_listings(account_id)
        """

        email = Validation.valid_email(email)

        account = self._account_db.get_by_email(email)
        if account is None:
            return None

        return self.get_account_with_listings(account.id)


    def get_account_with_listings_for(self, account: Account) -> Optional[Account]:
        """
        Wrapper:
            - Validate account object
            - Ensure account is persisted
            - Delegate to get_account_with_listings(account.id)
        """

        Validation.require_not_none(account, "account")

        if account.id is None:
            # Unpersisted account cannot have DB listings
            return None

        return self.get_account_with_listings(account.id)