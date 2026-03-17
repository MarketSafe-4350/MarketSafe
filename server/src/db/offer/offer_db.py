from abc import ABC, abstractmethod
from typing import List, Optional

from src.db.utils.db_utils import DBUtility
from src.domain_models.offer import Offer


class OfferDB(ABC):
    """
    Contract for Listing table persistence.

    IMPORTANT DESIGN RULES:
    - This layer is responsible ONLY for database access.
    - It does NOT contain business logic (authorization, ownership rules, etc.).
    - It does NOT decide HTTP responses.
    - It does NOT decide authentication logic.
    - It only performs CRUD + clearly-scoped queries.

    SECURITY / API SURFACE RULE:
    - Avoid "open-ended" search methods that accept many optional filters.
      Even if parameterized (SQL-safe), broad search surfaces often cause
      data-leak bugs at higher layers (e.g., forgetting authorization filters).
    - Prefer narrow, intention-revealing query methods that match real UI use-cases.

    Return conventions:
    - Methods that fetch a single row return Optional[Listing]:
        None is a valid state meaning "not found".
    - Methods that fetch multiple rows return List[Listing]:
        empty list is valid and MUST be returned when there are no results.


    ======================================================
    ERROR CONTRACT
    ======================================================

    All implementations MUST follow this error policy:

    1. Parameter validation failures:
       -> Raise ValidationError

    2. Record not found (when contract requires raising):
       -> Raise ListingNotFoundError

    3. Query-level SQL failures:
       -> Raise DatabaseQueryError

    4. Connection-level failures:
       -> Raised by DBUtility as DatabaseUnavailableError
          (Implementations should NOT catch/re-wrap those)
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
    def add(self, offer: Offer) -> Offer:
        """
        Insert a new offer row.

        Args:
            offer (Offer): The offer to insert.

        Returns:
            Offer: The created offer with the generated ID.

        Raises:
            ValidationError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    # --------------------------------------------------
    # READ
    # --------------------------------------------------
    @abstractmethod
    def get_by_id(self, offer_id: int) -> Optional[Offer]:
        """
        Fetch an offer by primary key.

        Args:
            offer_id (int): The ID of the offer.

        Returns:
            Optional[Offer]: The offer if found, or None if no row exists.
        """
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[Offer]:
        """
        Fetch all offers.

        Returns:
            List[Offer]: All offers, or empty list if the table is empty.
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_listing_id(self, listing_id: int) -> List[Offer]:
        """
        Fetch all offers for a given listing (all states).

        Args:
            listing_id (int): The ID of the listing.

        Returns:
            List[Offer]: A list of offers for the listing, or empty list if none found.
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_sender_id(self, sender_id: int) -> List[Offer]:
        """
        All offers that a user has SENT.

        Args:
            sender_id (int): The ID of the user who sent the offers.

        Returns:
            List[Offer]: A list of offers sent by the user, or empty list if none found.
        """
        raise NotImplementedError

    @abstractmethod
    def get_accepted_by_listing_id(self, listing_id: int) -> List[Offer]:
        """
        Fetch all accepted offers for a given listing.

        Args:
            listing_id (int): The ID of the listing.

        Returns:
            List[Offer]: A list of accepted offers for the listing, or empty list if none found.
        """
        raise NotImplementedError

    @abstractmethod
    def get_unseen_by_listing_id(self, listing_id: int) -> List[Offer]:
        """
        All unseen offers for a given listing.

        Args:
            listing_id (int): The ID of the listing.

        Returns:
            List[Offer]: A list of unseen offers for the listing.
        """
        raise NotImplementedError

    @abstractmethod
    def get_pending_by_listing_id(self, listing_id: int) -> List[Offer]:
        """
        All pending offers for a given listing.

        Args:
            listing_id (int): The ID of the listing.

        Returns:
            List[Offer]: A list of pending offers for the listing.
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_sender_and_listing(
        self, sender_id: int, listing_id: int
    ) -> Optional[Offer]:
        """
        Fetch the offer made by a specific sender on a specific listing.

        Args:
            sender_id (int): The ID of the sender.
            listing_id (int): The ID of the listing.

        Returns:
            Optional[Offer]: The offer if found, or None if no row exists.

        Constraints / notes:
        - Intended to enforce "one offer per sender per listing" at the service layer.
        - Used to check if a user has already made an offer on a listing.
        - Or further check if the offer is pending/accepted/rejected.
        """
        raise NotImplementedError

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------
    @abstractmethod
    def set_seen(self, offer_id: int) -> None:
        """Mark an offer as seen (seen = TRUE).

        Constraints / notes:
        - seen can only transition False -> True; always sets it to TRUE.
        - The one-way invariant is enforced by the domain model, not this layer.

        Raises:
            ValidationError
            OfferNotFoundError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    @abstractmethod
    def set_accepted(self, offer_id: int, accepted: bool) -> None:
        """Accept or reject an offer (accepted = TRUE or FALSE).

        Constraints / notes:
        - Does NOT enforce "only pending offers can be resolved".
          That invariant is enforced by higher layers.
        - accepted must be a bool (True = accepted, False = rejected).

        Raises:
            ValidationError
            OfferNotFoundError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------
    @abstractmethod
    def remove(self, offer_id: int) -> bool:
        """Delete an offer by ID.

        Expected behavior:
        - Return True if a row was deleted.
        - Return False if no row matched the ID.
        - Must NOT raise exception for "not found".

        Constraints / notes:
        - Higher layers must enforce that only the sender (or admin) can withdraw an offer.

        Raises:
            ValidationError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError
