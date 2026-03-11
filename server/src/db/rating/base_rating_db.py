# src/persistence/base_rating_db.py
from __future__ import annotations

from abc import ABC, abstractmethod

from src.db import DBUtility


class BaseRatingDB(ABC):
    """
    Lowest/base persistence contract for rating-related database access.

    Responsibilities:
    - Own the injected DBUtility instance
    - Define shared rating-stat query contracts

    NOTE:
    - These methods are abstract here.
    - They must be implemented by the concrete DB class,
      not by the middle RatingDB contract.
    """

    def __init__(self, db: DBUtility) -> None:
        self._db = db

    @abstractmethod
    def get_average_rating_by_account_id(self, account_id: int) -> float | None:
        """
        Return the average transaction rating received across all listings
        posted by this seller.

        Expected behavior:
        - Return float average if seller has rated/sold listings.
        - Return None if seller has no received ratings.
        - Raise exception on validation / database failure.
        """
        raise NotImplementedError


    @abstractmethod
    def get_sum_of_ratings_given_by_account_id(self, account_id: int) -> int:
        """
        Return the total sum of ratings given by a specific rater.

        Example:
        If the rater gave ratings [5,4,3] -> return 12.

        Returns:
        - integer sum
        - 0 if the rater has not rated anything
        """
        raise NotImplementedError

    @abstractmethod
    def get_sum_of_ratings_received_by_account_id(self, account_id: int) -> int:
        """
        Return the total sum of ratings received by a seller.

        The sum is calculated across all ratings associated with listings
        posted by the given account.

        IMPORTANT:
        - Only listings that actually have ratings are considered.
        - Listings without ratings are ignored.

        Example:
            Listing A rating = 5
            Listing B rating = 4
            Listing C has no rating

            Result = 9

        Expected behavior:
        - Return the sum of transaction_rating values for the seller.
        - Return 0 if the seller has no ratings.
        - Raise exception on validation or database failure.
        """
        raise NotImplementedError
