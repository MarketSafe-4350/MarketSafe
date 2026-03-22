from __future__ import annotations

from typing import Optional, List

from typing_extensions import override

from src.business_logic.managers.rating.abstract_rating_manager import IRatingManager
from src.db.rating import RatingDB
from src.domain_models import Rating
from src.utils import Validation


class RatingManager(IRatingManager):
    """
    Concrete business/service implementation for ratings.

    Responsibilities:
    - Validates inputs at the manager boundary
    - Delegates persistence work to RatingDB
    - Does not write SQL
    """

    def __init__(self, rating_db: RatingDB) -> None:
        super().__init__(rating_db)



    @override # pragma: no mutate
    def create_rating(self, rating: Rating) -> Rating:
        Validation.require_not_none(rating, "rating")
        return self._rating_db.add(rating)



    @override # pragma: no mutate
    def get_rating_by_id(self, rating_id: int) -> Optional[Rating]:
        rating_id = Validation.require_int(rating_id, "rating_id")
        return self._rating_db.get_by_id(rating_id)

    @override # pragma: no mutate
    def get_rating_by_listing_id(self, listing_id: int) -> Optional[Rating]:
        listing_id = Validation.require_int(listing_id, "listing_id")
        return self._rating_db.get_by_listing_id(listing_id)

    @override # pragma: no mutate
    def list_ratings_by_rater(self, rater_id: int) -> List[Rating]:
        rater_id = Validation.require_int(rater_id, "rater_id")
        return self._rating_db.get_by_rater_id(rater_id)

    @override # pragma: no mutate
    def list_ratings(self) -> List[Rating]:
        return self._rating_db.get_all()

    @override # pragma: no mutate
    def list_recent_ratings(self, limit: int = 50, offset: int = 0) -> List[Rating]:
        limit = Validation.require_int(limit, "limit")
        offset = Validation.require_int(offset, "offset")
        return self._rating_db.get_recent(limit=limit, offset=offset)

    @override # pragma: no mutate
    def list_ratings_by_score(self, transaction_rating: int) -> List[Rating]:
        transaction_rating = Validation.require_int(transaction_rating, "transaction_rating")
        return self._rating_db.get_by_score(transaction_rating)



    @override # pragma: no mutate
    def get_average_rating_by_account_id(self, account_id: int) -> float | None: # pragma: no mutate
        account_id = Validation.require_int(account_id, "account_id")
        return self._rating_db.get_average_rating_by_account_id(account_id)

    @override # pragma: no mutate
    def get_sum_of_ratings_given_by_account_id(self, account_id: int) -> int:
        account_id = Validation.require_int(account_id, "account_id")
        return self._rating_db.get_sum_of_ratings_given_by_account_id(account_id)

    @override # pragma: no mutate
    def get_sum_of_ratings_received_by_account_id(self, account_id: int) -> int:
        account_id = Validation.require_int(account_id, "account_id")
        return self._rating_db.get_sum_of_ratings_received_by_account_id(account_id)

    @override # pragma: no mutate
    def get_average_for_rater(self, rater_id: int) -> float | None: # pragma: no mutate
        rater_id = Validation.require_int(rater_id, "rater_id")
        return self._rating_db.get_average_for_rater(rater_id)

    @override # pragma: no mutate
    def count_by_rater(self, rater_id: int) -> int:
        rater_id = Validation.require_int(rater_id, "rater_id")
        return self._rating_db.count_by_rater(rater_id)



    @override # pragma: no mutate
    def update_rating(self, rating: Rating) -> Rating:
        Validation.require_not_none(rating, "rating")
        Validation.require_int(rating.id, "rating_id")
        return self._rating_db.update(rating)

    @override # pragma: no mutate
    def update_rating_score(self, rating_id: int, transaction_rating: int) -> None:
        rating_id = Validation.require_int(rating_id, "rating_id")
        transaction_rating = Validation.require_int(transaction_rating, "transaction_rating")
        self._rating_db.set_score(rating_id, transaction_rating)



    @override # pragma: no mutate
    def delete_rating(self, rating_id: int) -> bool:
        rating_id = Validation.require_int(rating_id, "rating_id")
        return self._rating_db.remove(rating_id)

    @override # pragma: no mutate
    def delete_rating_by_listing_id(self, listing_id: int) -> bool:
        listing_id = Validation.require_int(listing_id, "listing_id")
        return self._rating_db.remove_by_listing_id(listing_id)
