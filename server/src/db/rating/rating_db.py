# src/persistence/rating_db.py
from __future__ import annotations

from abc import abstractmethod
from typing import List, Optional

from src.db.rating.base_rating_db import BaseRatingDB
from src.domain_models import Rating


class RatingDB(BaseRatingDB):
    """
    Contract for Rating table persistence.

    IMPORTANT DESIGN RULES:
    - This layer is responsible ONLY for database access.
    - It does NOT contain business logic.
    - It does NOT decide HTTP responses.
    - It does NOT decide authentication logic.
    - It only performs CRUD + clearly-scoped queries.

    DOMAIN / SCHEMA NOTES:
    - A rating belongs to exactly one listing.
    - A rating is created by exactly one account (rater_id).
    - The database enforces at most ONE rating per listing:
          UNIQUE(listing_id)
    - The database trigger enforces:
          * listing must already be sold
          * rater_id must match listing.sold_to_id

    Return conventions:
    - Methods that fetch a single row return Optional[Rating]:
        None is a valid state meaning "not found".
    - Methods that fetch multiple rows return List[Rating]:
        empty list is valid and MUST be returned when there are no results.


    ======================================================
    ERROR CONTRACT
    ======================================================

    All implementations MUST follow this error policy:

    1. Parameter validation failures:
       -> Raise ValidationError

    2. Record not found (when contract requires raising):
       -> Raise RatingNotFoundError

    3. Query-level SQL failures:
       -> Raise DatabaseQueryError

    4. Connection-level failures:
       -> Raised by DBUtility as DatabaseUnavailableError
          (Implementations should NOT catch/re-wrap those)
    """



    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------

    @abstractmethod
    def add(self, rating: Rating) -> Rating:
        """
        Insert a new rating row.

        Expected behavior:
        - Must insert the rating into the database.
        - Must return the created Rating with the generated ID.
        - Must raise an exception if:
            - listing_id does not exist
            - rater_id does not exist
            - a rating already exists for the same listing
            - the listing is not sold
            - rater_id is not the buyer of the listing
            - Database is unavailable
            - Any SQL error occurs

        Constraints / notes:
        - created_at is DB-managed (DEFAULT CURRENT_TIMESTAMP).
        - transaction_rating is required.
        - Business rules are enforced by DB constraints/triggers,
          but higher layers may still validate earlier for UX.

        Never returns None.

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
    def get_by_id(self, rating_id: int) -> Optional[Rating]:
        """
        Fetch rating by primary key.

        Expected behavior:
        - Return Rating if a row exists.
        - Return None if no row is found.
        - Must NOT raise exception for "not found".
        - Must raise exception if a database error occurs.

        Raises:
            ValidationError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError



    @abstractmethod
    def get_all(self) -> List[Rating]:
        """
        Fetch all ratings.

        Expected behavior:
        - Return an empty list if the table is empty.
        - Never return None.
        - Must raise an exception if a database error occurs.

        Raises:
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    @abstractmethod
    def get_recent(self, limit: int = 50, offset: int = 0) -> List[Rating]:
        """
        Fetch ratings ordered by newest first with pagination.

        Expected behavior:
        - Return empty list when no rows match.
        - Must raise exception if a database error occurs.

        Constraints / notes:
        - limit and offset must be integers.
        - Higher layers may enforce a max limit.

        Raises:
            ValidationError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_score(self, transaction_rating: int) -> List[Rating]:
        """
        Fetch all ratings with an exact score.

        Expected behavior:
        - Return empty list when no rows match.
        - Must raise exception if a database error occurs.

        Constraints / notes:
        - transaction_rating should be within the valid domain expected
          by the application (for example 1..5 if that is your rule).
        - The persistence layer should validate type/basic shape only.
          More detailed business validation may also happen above.

        Raises:
            ValidationError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    # --------------------------------------------------
    # AGGREGATE / SUMMARY QUERIES
    # --------------------------------------------------

    @abstractmethod
    def get_average_for_rater(self, rater_id: int) -> Optional[float]:
        """
        Get the average rating value for ratings created by a given account.

        Expected behavior:
        - Return a float average if rows exist.
        - Return None if the account has not created any ratings.
        - Must raise exception if a database error occurs.

        Constraints / notes:
        - This is a database summary query, not business logic.

        Raises:
            ValidationError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    @abstractmethod
    def count_by_rater(self, rater_id: int) -> int:
        """
        Count how many ratings were created by a given account.

        Expected behavior:
        - Return 0 if none exist.
        - Never return None.
        - Must raise exception if a database error occurs.

        Raises:
            ValidationError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    @abstractmethod
    def update(self, rating: Rating) -> Rating:
        """
        Update an existing rating row.

        Expected behavior:
        - Must update the row for rating.id.
        - Must return the updated Rating (typically via re-read).
        - If rating.id does not exist:
              raise RatingNotFoundError
        - Must raise an exception if a database error occurs.

        Constraints / notes:
        - Updating listing_id or rater_id may still be subject to
          DB trigger / FK / UNIQUE constraints.
        - Higher layers may choose to restrict what fields are editable.
          This layer only performs persistence.

        Raises:
            ValidationError
            RatingNotFoundError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    @abstractmethod
    def set_score(self, rating_id: int, transaction_rating: int) -> None:
        """
        Update only the transaction_rating value.

        Expected behavior:
        - Update the transaction_rating column for the rating_id.
        - If rating_id does not exist:
              raise RatingNotFoundError
        - Must raise an exception if a database error occurs.

        Constraints / notes:
        - transaction_rating must be a valid integer score.

        Raises:
            ValidationError
            RatingNotFoundError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------

    @abstractmethod
    def remove(self, rating_id: int) -> bool:
        """
        Delete a rating by ID.

        Expected behavior:
        - Return True if a row was deleted.
        - Return False if no row matched the ID.
        - Must NOT raise exception for "not found".
        - Must raise exception for database errors.

        Raises:
            ValidationError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    @abstractmethod
    def remove_by_listing_id(self, listing_id: int) -> bool:
        """
        Delete the rating associated with a listing.

        Expected behavior:
        - Return True if a row was deleted.
        - Return False if the listing had no rating.
        - Must NOT raise exception for "not found".
        - Must raise exception for database errors.

        Constraints / notes:
        - Because listing_id is UNIQUE in rating, at most one row is deleted.

        Raises:
            ValidationError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError
