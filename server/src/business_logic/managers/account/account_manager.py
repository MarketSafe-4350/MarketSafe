from __future__ import annotations
from typing import Optional, List

from typing_extensions import override

from src.business_logic.managers.account import IAccountManager
from src.db.account import AccountDB
from src.db.listing import ListingDB
from src.db.rating import BaseRatingDB
from src.domain_models import Account
from src.utils import Validation, AccountAlreadyExistsError, AccountNotFoundError, ConfigurationError


class AccountManager(IAccountManager):
    """
    Concrete business/service implementation.

    - Validates inputs
    - Enforces business rules (unique email, etc.)
    - Delegates SQL work to AccountDB

     - Optionally enriches Account objects with:
        * average_rating_received
        * sum_of_ratings_received
      when BaseRatingDB dependency is provided
    """

    def __init__(
            self,
            account_db: AccountDB,
            listing_db: Optional[ListingDB] = None,
            rating_db: Optional[BaseRatingDB] = None,
    ) -> None:
        super().__init__(account_db, listing_db, rating_db)

    @override
    def create_account(self, account: Account) -> Account:
        Validation.require_not_none(account, "account")

        existing = self._account_db.get_by_email(account.email)
        if existing is not None:
            raise AccountAlreadyExistsError(
                message=f"Account already exists for email: {account.email}",
                details={"email": account.email},
            )

        created = self._account_db.add(Account(
            account_id=None,
            email=account.email,
            password=account.password,
            fname=account.fname.strip(),
            lname=account.lname.strip(),
            verified=bool(account.verified),
        ))

        return self._populate_rating_values_if_available(created)

    # ==================================================
    # READ
    # ==================================================

    @override
    def get_account_by_id(self, account_id: int) -> Optional[Account]:
        Validation.require_int(account_id, "account_id")
        account = self._account_db.get_by_id(account_id)
        return self._populate_rating_values_if_available(account)

    @override
    def get_account_by_email(self, email: str) -> Optional[Account]:
        email = Validation.valid_email(email)
        account = self._account_db.get_by_email(email)
        return self._populate_rating_values_if_available(account)

    @override
    def list_accounts(self) -> List[Account]:
        accounts = self._account_db.get_all()

        for account in accounts:
            self._populate_rating_values_if_available(account)

        return accounts

    @override
    def set_verified(self, account_id: int, verified: bool) -> None:
        Validation.require_int(account_id, "account_id")
        Validation.is_boolean(verified, "verified")
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

        # ==================================================
        # LISTING ORCHESTRATION
        # ==================================================

    @override
    def get_account_with_listings(self, account_id: int) -> Optional[Account]:
        """
        Orchestration:
          - account_db.get_by_id(account_id)
          - listing_db.get_by_seller_id(account_id)
          - attach listings to Account via account.add_listing(...)
          - optionally attach rating aggregates if rating DB exists
          - return Account (or None if not found)
        """
        account_id = Validation.require_int(account_id, "account_id")

        if self._listing_db is None:
            raise ConfigurationError(
                message="ListingDB dependency is required for get_account_with_listings().",
                details={"missing_dependency": "ListingDB"},
            )

        account = self._account_db.get_by_id(account_id)
        if account is None:
            return None

        listings = self._listing_db.get_by_seller_id(account_id)

        for listing in listings:
            account.add_listing(listing)

        return self._populate_rating_values_if_available(account)

    @override
    def get_account_with_listings_by_email(self, email: str) -> Optional[Account]:
        """
        Wrapper:
            - Normalize/validate email
            - Fetch account by email
            - Delegate to get_account_with_listings(account.id)
        """
        email = Validation.valid_email(email)

        account = self._account_db.get_by_email(email)
        if account is None:
            return None

        return self.get_account_with_listings(account.id)

    @override
    def get_account_with_listings_for(self, account: Account) -> Optional[Account]:
        """
        Wrapper:
            - Validate account object
            - Ensure account is persisted
            - Delegate to get_account_with_listings(account.id)
        """
        Validation.require_not_none(account, "account")

        if account.id is None:
            return None

        return self.get_account_with_listings(account.id)

    # ==================================================
    # RATING AGGREGATE ORCHESTRATION
    # ==================================================
    @override
    def fill_account_rating_values(self, account: Account) -> Account:
        """
        Populate average_rating_received and sum_of_ratings_received
        on an existing Account instance.

        Raises:
        - ConfigurationError if RatingDB dependency is missing
        """
        Validation.require_not_none(account, "account")

        if self._rating_db is None:
            raise ConfigurationError(
                message="RatingDB dependency is required for fill_account_rating_values().",
                details={"missing_dependency": "BaseRatingDB"},
            )

        if account.id is None:
            return account

        account.average_rating_received = self._rating_db.get_average_rating_by_account_id(account.id)
        account.sum_of_ratings_received = self._rating_db.get_sum_of_ratings_received_by_account_id(account.id)
        return account

    @override
    def get_account_with_rating_values_by_id(self, account_id: int) -> Optional[Account]:
        """
        Fetch account by id and populate rating aggregate values.

        Raises:
        - ConfigurationError if RatingDB dependency is missing
        """
        Validation.require_int(account_id, "account_id")

        if self._rating_db is None:
            raise ConfigurationError(
                message="RatingDB dependency is required for get_account_with_rating_values_by_id().",
                details={"missing_dependency": "BaseRatingDB"},
            )

        account = self._account_db.get_by_id(account_id)
        if account is None:
            return None

        return self.fill_account_rating_values(account)

    @override
    def get_account_with_rating_values_by_email(self, email: str) -> Optional[Account]:
        """
        Fetch account by email and populate rating aggregate values.

        Raises:
        - ConfigurationError if RatingDB dependency is missing
        """
        email = Validation.valid_email(email)

        if self._rating_db is None:
            raise ConfigurationError(
                message="RatingDB dependency is required for get_account_with_rating_values_by_email().",
                details={"missing_dependency": "BaseRatingDB"},
            )

        account = self._account_db.get_by_email(email)
        if account is None:
            return None

        return self.fill_account_rating_values(account)

        # ==================================================
        # INTERNAL HELPERS
        # ==================================================

    def _populate_rating_values_if_available(self, account: Optional[Account]) -> Optional[Account]:
        """
        Populate rating aggregate fields on the given Account if RatingDB is available.

        Behavior:
        - If account is None -> return None
        - If rating DB is not configured -> return account unchanged
        - Otherwise populate:
            * average_rating_received
            * sum_of_ratings_received
        """
        if account is None:
            return None

        if self._rating_db is None:
            return account

        if account.id is None:
            return account

        account.average_rating_received = self._rating_db.get_average_rating_by_account_id(account.id)
        account.sum_of_ratings_received = self._rating_db.get_sum_of_ratings_received_by_account_id(account.id)
        return account
