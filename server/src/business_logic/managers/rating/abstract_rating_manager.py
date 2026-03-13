from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, List

from src.db.rating import RatingDB
from src.domain_models import Rating
from src.utils import Validation


class IRatingManager(ABC):
    """
    Rating business layer contract (manager/service).

    Responsibilities:
        - Contains business logic and orchestration.
        - Calls persistence layer (RatingDB) to read/write data.
        - Decides which domain errors to raise (404/409/422/etc.).
        - Does NOT write SQL.

    Dependency contract:
        - rating_db: RatingDB (required)

    Notes:
        - RatingDB already includes BaseRatingDB behavior through inheritance.
        - This manager contract exposes both:
            * aggregate/statistic methods
            * CRUD/query methods
    """

    def __init__(self, rating_db: RatingDB) -> None:
        Validation.require_not_none(rating_db, "rating_db")
        self._rating_db = rating_db

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------

    @abstractmethod
    def create_rating(self, rating: Rating) -> Rating:
        """
        PURPOSE:
            Create a new rating.

        EXPECTED BEHAVIOR:
            - Accept a Rating object (should already be structurally valid).
            - Enforce any business rules required before creation.
            - Persist the rating using RatingDB.add().
            - Return the created Rating with generated database ID.

        RETURNS:
            Rating

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
            - Domain-specific conflict/constraint errors if applicable
        """
        raise NotImplementedError

    # --------------------------------------------------
    # READ (simple)
    # --------------------------------------------------

    @abstractmethod
    def get_rating_by_id(self, rating_id: int) -> Optional[Rating]:
        """
        PURPOSE:
            Fetch a rating by its database ID.

        EXPECTED BEHAVIOR:
            - Return Rating if it exists.
            - Return None if not found.
            - Must NOT raise RatingNotFoundError for normal read miss.

        RETURNS:
            Rating | None

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def get_rating_by_listing_id(self, listing_id: int) -> Optional[Rating]:
        """
        PURPOSE:
            Fetch the rating associated with a listing.

        EXPECTED BEHAVIOR:
            - Return Rating if one exists.
            - Return None if the listing has no rating.
            - Must NOT raise RatingNotFoundError for normal read miss.

        RETURNS:
            Rating | None

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def list_ratings_by_rater(self, rater_id: int) -> List[Rating]:
        """
        PURPOSE:
            List all ratings created by a specific rater/account.

        EXPECTED BEHAVIOR:
            - Return list of ratings.
            - Return empty list if none exist.
            - Never return None.

        RETURNS:
            list[Rating]

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def list_ratings(self) -> List[Rating]:
        """
        PURPOSE:
            List all ratings.

        EXPECTED BEHAVIOR:
            - Return list of ratings.
            - Return empty list if none exist.
            - Never return None.

        RETURNS:
            list[Rating]

        RAISES (typical):
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def list_recent_ratings(self, limit: int = 50, offset: int = 0) -> List[Rating]:
        """
        PURPOSE:
            Fetch ratings ordered by newest first with pagination.

        EXPECTED BEHAVIOR:
            - Return list of ratings.
            - Return empty list if none exist.
            - Never return None.

        RETURNS:
            list[Rating]

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def list_ratings_by_score(self, transaction_rating: int) -> List[Rating]:
        """
        PURPOSE:
            Fetch all ratings with the given score.

        EXPECTED BEHAVIOR:
            - Return list of ratings.
            - Return empty list if none exist.
            - Never return None.

        RETURNS:
            list[Rating]

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    # --------------------------------------------------
    # READ (aggregate / statistics)
    # --------------------------------------------------

    @abstractmethod
    def get_average_rating_by_account_id(self, account_id: int) -> float | None:
        """
        PURPOSE:
            Get the average rating received by a seller/account.

        EXPECTED BEHAVIOR:
            - Return float average when ratings exist.
            - Return None if no ratings exist for that seller.

        RETURNS:
            float | None

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def get_sum_of_ratings_given_by_account_id(self, account_id: int) -> int:
        """
        PURPOSE:
            Get the total sum of ratings given by a rater/account.

        EXPECTED BEHAVIOR:
            - Return integer sum.
            - Return 0 if the account has not given any ratings.

        RETURNS:
            int

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def get_sum_of_ratings_received_by_account_id(self, account_id: int) -> int:
        """
        PURPOSE:
            Get the total sum of ratings received by a seller/account.

        EXPECTED BEHAVIOR:
            - Only listings that actually have ratings are counted.
            - Listings without ratings are ignored.
            - Return 0 if the seller has no ratings.

        RETURNS:
            int

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def get_average_for_rater(self, rater_id: int) -> float | None:
        """
        PURPOSE:
            Get the average score of ratings created by a rater/account.

        EXPECTED BEHAVIOR:
            - Return float average if ratings exist.
            - Return None if the rater has not created any ratings.

        RETURNS:
            float | None

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def count_by_rater(self, rater_id: int) -> int:
        """
        PURPOSE:
            Count how many ratings were created by a rater/account.

        EXPECTED BEHAVIOR:
            - Return count as integer.
            - Return 0 if no ratings exist.

        RETURNS:
            int

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    @abstractmethod
    def update_rating(self, rating: Rating) -> Rating:
        """
        PURPOSE:
            Update an existing rating.

        EXPECTED BEHAVIOR:
            - Requires rating.id to be present.
            - Calls RatingDB.update(rating).
            - Raises RatingNotFoundError if the rating does not exist.

        RETURNS:
            Rating

        RAISES (typical):
            - ValidationError
            - RatingNotFoundError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def update_rating_score(self, rating_id: int, transaction_rating: int) -> None:
        """
        PURPOSE:
            Update only the score of a rating.

        EXPECTED BEHAVIOR:
            - Calls RatingDB.set_score(rating_id, transaction_rating).
            - Raises RatingNotFoundError if the rating does not exist.

        RETURNS:
            None

        RAISES (typical):
            - ValidationError
            - RatingNotFoundError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------

    @abstractmethod
    def delete_rating(self, rating_id: int) -> bool:
        """
        PURPOSE:
            Delete a rating by ID.

        EXPECTED BEHAVIOR:
            - Return True if deleted.
            - Return False if not found.
            - Must NOT raise RatingNotFoundError for missing row.

        RETURNS:
            bool

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def delete_rating_by_listing_id(self, listing_id: int) -> bool:
        """
        PURPOSE:
            Delete the rating associated with a listing.

        EXPECTED BEHAVIOR:
            - Return True if deleted.
            - Return False if no rating exists for the listing.
            - Must NOT raise RatingNotFoundError for missing row.

        RETURNS:
            bool

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError