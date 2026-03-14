from __future__ import annotations

import unittest
from uuid import uuid4

from sqlalchemy import text

from src.business_logic.managers.rating.rating_manager import RatingManager
from src.db.rating.mysql import MySQLRatingDB
from src.domain_models import Rating
from src.utils import RatingNotFoundError, ValidationError
from tests.helpers.integration_db import ensure_tables_exist, reset_all_tables
from tests.helpers.integration_db_session import acquire, get_db, release


class TestRatingManagerIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls._session = acquire(timeout_s=60)
        cls._db = get_db()

        ensure_tables_exist(cls._db, timeout_s=60)
        reset_all_tables(cls._db)

        cls._rating_db = MySQLRatingDB(cls._db)
        cls._manager = RatingManager(cls._rating_db)

    @classmethod
    def tearDownClass(cls) -> None:
        release(cls._session, remove_volumes=False)

    def setUp(self) -> None:
        reset_all_tables(self._db)

    # --------------------------------------------------
    # helpers
    # --------------------------------------------------
    def _insert_account(self, verified: bool = True) -> int:
        uniq = uuid4().hex[:10]

        sql = text("""
            INSERT INTO account (email, password, fname, lname, verified)
            VALUES (:email, :password, :fname, :lname, :verified)
        """)

        with self._db.transaction() as conn:
            result = conn.execute(sql, {
                "email": f"rating_mgr_{uniq}@example.com",
                "password": "pass",
                "fname": "Test",
                "lname": "User",
                "verified": verified,
            })
            return int(result.lastrowid)

    def _insert_listing(
        self,
        seller_id: int,
        *,
        sold_to_id: int | None = None,
        is_sold: bool = False,
        price: float = 100.0,
    ) -> int:
        uniq = uuid4().hex[:8]

        sql = text("""
            INSERT INTO listing (
                seller_id,
                title,
                description,
                price,
                location,
                image_url,
                is_sold,
                sold_to_id
            )
            VALUES (
                :seller_id,
                :title,
                :description,
                :price,
                :location,
                :image_url,
                :is_sold,
                :sold_to_id
            )
        """)

        with self._db.transaction() as conn:
            result = conn.execute(sql, {
                "seller_id": seller_id,
                "title": f"Listing {uniq}",
                "description": "Test listing",
                "price": price,
                "location": "Winnipeg",
                "image_url": None,
                "is_sold": is_sold,
                "sold_to_id": sold_to_id,
            })
            return int(result.lastrowid)

    def _new_rating(self, score: int = 5) -> Rating:
        seller_id = self._insert_account()
        buyer_id = self._insert_account()
        listing_id = self._insert_listing(
            seller_id,
            sold_to_id=buyer_id,
            is_sold=True,
        )

        return Rating(
            listing_id=listing_id,
            rater_id=buyer_id,
            transaction_rating=score,
        )

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------
    def test_create_rating_persists_and_returns_id(self) -> None:
        rating = self._new_rating(score=5)

        created = self._manager.create_rating(rating)
        self.assertIsNotNone(created.id)
        self.assertEqual(created.listing_id, rating.listing_id)
        self.assertEqual(created.rater_id, rating.rater_id)
        self.assertEqual(created.transaction_rating, rating.transaction_rating)

        fetched = self._manager.get_rating_by_id(created.id)
        self.assertIsNotNone(fetched)
        assert fetched is not None

        self.assertEqual(fetched.id, created.id)
        self.assertEqual(fetched.listing_id, created.listing_id)
        self.assertEqual(fetched.rater_id, created.rater_id)
        self.assertEqual(fetched.transaction_rating, created.transaction_rating)

    def test_create_rating_none_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            self._manager.create_rating(None)  # type: ignore[arg-type]

    # --------------------------------------------------
    # READ (simple)
    # --------------------------------------------------
    def test_get_rating_by_id_happy_path(self) -> None:
        created = self._manager.create_rating(self._new_rating(score=4))

        fetched = self._manager.get_rating_by_id(created.id)
        self.assertIsNotNone(fetched)
        assert fetched is not None

        self.assertEqual(fetched.id, created.id)
        self.assertEqual(fetched.transaction_rating, 4)

    def test_get_rating_by_id_missing_returns_none(self) -> None:
        out = self._manager.get_rating_by_id(999999)
        self.assertIsNone(out)

    def test_get_rating_by_id_invalid_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            self._manager.get_rating_by_id("bad")  # type: ignore[arg-type]

    def test_get_rating_by_listing_id_happy_path(self) -> None:
        created = self._manager.create_rating(self._new_rating(score=3))

        fetched = self._manager.get_rating_by_listing_id(created.listing_id)
        self.assertIsNotNone(fetched)
        assert fetched is not None

        self.assertEqual(fetched.id, created.id)
        self.assertEqual(fetched.listing_id, created.listing_id)

    def test_get_rating_by_listing_id_missing_returns_none(self) -> None:
        out = self._manager.get_rating_by_listing_id(999999)
        self.assertIsNone(out)

    def test_get_rating_by_listing_id_invalid_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            self._manager.get_rating_by_listing_id(None)  # type: ignore[arg-type]

    def test_list_ratings_by_rater_happy_path(self) -> None:
        seller_1 = self._insert_account()
        seller_2 = self._insert_account()
        buyer_id = self._insert_account()

        listing_1 = self._insert_listing(seller_1, sold_to_id=buyer_id, is_sold=True)
        listing_2 = self._insert_listing(seller_2, sold_to_id=buyer_id, is_sold=True)

        self._manager.create_rating(Rating(
            listing_id=listing_1,
            rater_id=buyer_id,
            transaction_rating=5,
        ))
        self._manager.create_rating(Rating(
            listing_id=listing_2,
            rater_id=buyer_id,
            transaction_rating=2,
        ))

        ratings = self._manager.list_ratings_by_rater(buyer_id)
        self.assertEqual(len(ratings), 2)
        for rating in ratings:
            self.assertEqual(rating.rater_id, buyer_id)

    def test_list_ratings_by_rater_empty_returns_empty_list(self) -> None:
        account_id = self._insert_account()

        ratings = self._manager.list_ratings_by_rater(account_id)
        self.assertEqual(ratings, [])

    def test_list_ratings_by_rater_invalid_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            self._manager.list_ratings_by_rater("bad")  # type: ignore[arg-type]

    def test_list_ratings_returns_all_rows(self) -> None:
        self._manager.create_rating(self._new_rating(score=5))
        self._manager.create_rating(self._new_rating(score=1))

        ratings = self._manager.list_ratings()
        self.assertEqual(len(ratings), 2)

    def test_list_recent_ratings_happy_path(self) -> None:
        r1 = self._manager.create_rating(self._new_rating(score=1))
        r2 = self._manager.create_rating(self._new_rating(score=2))
        r3 = self._manager.create_rating(self._new_rating(score=3))

        recent = self._manager.list_recent_ratings(limit=2, offset=0)
        self.assertEqual(len(recent), 2)
        self.assertEqual([r.id for r in recent], [r3.id, r2.id])

        recent_offset = self._manager.list_recent_ratings(limit=1, offset=1)
        self.assertEqual(len(recent_offset), 1)
        self.assertEqual(recent_offset[0].id, r2.id)

        _ = r1

    def test_list_recent_ratings_invalid_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            self._manager.list_recent_ratings(limit="bad", offset=0)  # type: ignore[arg-type]

        with self.assertRaises(ValidationError):
            self._manager.list_recent_ratings(limit=10, offset=None)  # type: ignore[arg-type]

    def test_list_ratings_by_score_happy_path(self) -> None:
        self._manager.create_rating(self._new_rating(score=5))
        self._manager.create_rating(self._new_rating(score=2))
        self._manager.create_rating(self._new_rating(score=5))

        ratings = self._manager.list_ratings_by_score(5)
        self.assertEqual(len(ratings), 2)
        for rating in ratings:
            self.assertEqual(rating.transaction_rating, 5)

    def test_list_ratings_by_score_invalid_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            self._manager.list_ratings_by_score("bad")  # type: ignore[arg-type]

    # --------------------------------------------------
    # READ (aggregate / statistics)
    # --------------------------------------------------
    def test_get_average_rating_by_account_id_happy_path(self) -> None:
        seller_id = self._insert_account()
        buyer_1 = self._insert_account()
        buyer_2 = self._insert_account()

        listing_1 = self._insert_listing(seller_id, sold_to_id=buyer_1, is_sold=True)
        listing_2 = self._insert_listing(seller_id, sold_to_id=buyer_2, is_sold=True)

        self._manager.create_rating(Rating(
            listing_id=listing_1,
            rater_id=buyer_1,
            transaction_rating=4,
        ))
        self._manager.create_rating(Rating(
            listing_id=listing_2,
            rater_id=buyer_2,
            transaction_rating=2,
        ))

        avg = self._manager.get_average_rating_by_account_id(seller_id)
        self.assertEqual(avg, 3.0)

    def test_get_average_rating_by_account_id_returns_none_when_no_ratings(self) -> None:
        seller_id = self._insert_account()

        avg = self._manager.get_average_rating_by_account_id(seller_id)
        self.assertIsNone(avg)

    def test_get_average_rating_by_account_id_invalid_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            self._manager.get_average_rating_by_account_id(None)  # type: ignore[arg-type]

    def test_get_sum_of_ratings_given_by_account_id_happy_path(self) -> None:
        seller_1 = self._insert_account()
        seller_2 = self._insert_account()
        buyer_id = self._insert_account()

        listing_1 = self._insert_listing(seller_1, sold_to_id=buyer_id, is_sold=True)
        listing_2 = self._insert_listing(seller_2, sold_to_id=buyer_id, is_sold=True)

        self._manager.create_rating(Rating(
            listing_id=listing_1,
            rater_id=buyer_id,
            transaction_rating=5,
        ))
        self._manager.create_rating(Rating(
            listing_id=listing_2,
            rater_id=buyer_id,
            transaction_rating=3,
        ))

        total = self._manager.get_sum_of_ratings_given_by_account_id(buyer_id)
        self.assertEqual(total, 8)

    def test_get_sum_of_ratings_given_by_account_id_invalid_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            self._manager.get_sum_of_ratings_given_by_account_id("bad")  # type: ignore[arg-type]

    def test_get_sum_of_ratings_received_by_account_id_happy_path(self) -> None:
        seller_id = self._insert_account()
        buyer_1 = self._insert_account()
        buyer_2 = self._insert_account()

        listing_1 = self._insert_listing(seller_id, sold_to_id=buyer_1, is_sold=True)
        listing_2 = self._insert_listing(seller_id, sold_to_id=buyer_2, is_sold=True)

        self._manager.create_rating(Rating(
            listing_id=listing_1,
            rater_id=buyer_1,
            transaction_rating=1,
        ))
        self._manager.create_rating(Rating(
            listing_id=listing_2,
            rater_id=buyer_2,
            transaction_rating=4,
        ))

        total = self._manager.get_sum_of_ratings_received_by_account_id(seller_id)
        self.assertEqual(total, 5)

    def test_get_sum_of_ratings_received_by_account_id_invalid_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            self._manager.get_sum_of_ratings_received_by_account_id("bad")  # type: ignore[arg-type]

    def test_get_average_for_rater_happy_path(self) -> None:
        seller_1 = self._insert_account()
        seller_2 = self._insert_account()
        buyer_id = self._insert_account()

        listing_1 = self._insert_listing(seller_1, sold_to_id=buyer_id, is_sold=True)
        listing_2 = self._insert_listing(seller_2, sold_to_id=buyer_id, is_sold=True)

        self._manager.create_rating(Rating(
            listing_id=listing_1,
            rater_id=buyer_id,
            transaction_rating=5,
        ))
        self._manager.create_rating(Rating(
            listing_id=listing_2,
            rater_id=buyer_id,
            transaction_rating=1,
        ))

        avg = self._manager.get_average_for_rater(buyer_id)
        self.assertEqual(avg, 3.0)

    def test_get_average_for_rater_returns_none_when_no_ratings(self) -> None:
        account_id = self._insert_account()

        avg = self._manager.get_average_for_rater(account_id)
        self.assertIsNone(avg)

    def test_get_average_for_rater_invalid_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            self._manager.get_average_for_rater(None)  # type: ignore[arg-type]

    def test_count_by_rater_happy_path(self) -> None:
        seller_1 = self._insert_account()
        seller_2 = self._insert_account()
        buyer_id = self._insert_account()

        listing_1 = self._insert_listing(seller_1, sold_to_id=buyer_id, is_sold=True)
        listing_2 = self._insert_listing(seller_2, sold_to_id=buyer_id, is_sold=True)

        self._manager.create_rating(Rating(
            listing_id=listing_1,
            rater_id=buyer_id,
            transaction_rating=5,
        ))
        self._manager.create_rating(Rating(
            listing_id=listing_2,
            rater_id=buyer_id,
            transaction_rating=4,
        ))

        count = self._manager.count_by_rater(buyer_id)
        self.assertEqual(count, 2)

    def test_count_by_rater_invalid_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            self._manager.count_by_rater("bad")  # type: ignore[arg-type]

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------
    def test_update_rating_happy_path(self) -> None:
        created = self._manager.create_rating(self._new_rating(score=2))

        updated_input = Rating(
            listing_id=created.listing_id,
            rater_id=created.rater_id,
            transaction_rating=5,
            rating_id=created.id,
        )

        updated = self._manager.update_rating(updated_input)
        self.assertEqual(updated.id, created.id)
        self.assertEqual(updated.transaction_rating, 5)

    def test_update_rating_missing_raises(self) -> None:
        missing = Rating(
            listing_id=1,
            rater_id=1,
            transaction_rating=4,
            rating_id=999999,
        )

        with self.assertRaises(RatingNotFoundError):
            self._manager.update_rating(missing)

    def test_update_rating_none_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            self._manager.update_rating(None)  # type: ignore[arg-type]

    def test_update_rating_unpersisted_raises_validation_error(self) -> None:
        rating = Rating(
            listing_id=1,
            rater_id=1,
            transaction_rating=4,
        )

        with self.assertRaises(ValidationError):
            self._manager.update_rating(rating)

    def test_update_rating_score_happy_path(self) -> None:
        created = self._manager.create_rating(self._new_rating(score=2))

        self._manager.update_rating_score(created.id, 4)

        fetched = self._manager.get_rating_by_id(created.id)
        self.assertIsNotNone(fetched)
        assert fetched is not None
        self.assertEqual(fetched.transaction_rating, 4)

    def test_update_rating_score_missing_raises(self) -> None:
        with self.assertRaises(RatingNotFoundError):
            self._manager.update_rating_score(999999, 4)

    def test_update_rating_score_invalid_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            self._manager.update_rating_score("bad", 4)  # type: ignore[arg-type]

        with self.assertRaises(ValidationError):
            self._manager.update_rating_score(1, None)  # type: ignore[arg-type]

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------
    def test_delete_rating_happy_path(self) -> None:
        created = self._manager.create_rating(self._new_rating(score=5))

        deleted = self._manager.delete_rating(created.id)
        self.assertTrue(deleted)

        deleted_again = self._manager.delete_rating(created.id)
        self.assertFalse(deleted_again)

    def test_delete_rating_invalid_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            self._manager.delete_rating(None)  # type: ignore[arg-type]

    def test_delete_rating_by_listing_id_happy_path(self) -> None:
        created = self._manager.create_rating(self._new_rating(score=5))

        deleted = self._manager.delete_rating_by_listing_id(created.listing_id)
        self.assertTrue(deleted)

        deleted_again = self._manager.delete_rating_by_listing_id(created.listing_id)
        self.assertFalse(deleted_again)

    def test_delete_rating_by_listing_id_invalid_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            self._manager.delete_rating_by_listing_id("bad")  # type: ignore[arg-type]