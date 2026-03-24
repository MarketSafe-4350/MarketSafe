from __future__ import annotations

import unittest
from uuid import uuid4

from sqlalchemy import text

from src.db.rating.mysql import MySQLRatingDB
from src.domain_models import Rating
from src.utils import DatabaseQueryError, RatingNotFoundError
from tests.helpers.integration_db import ensure_tables_exist, reset_all_tables
from tests.helpers.integration_db_session import acquire, get_db, release


class TestMySQLRatingDB(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls._session = acquire(timeout_s=60)
        cls._db = get_db()

        ensure_tables_exist(cls._db, timeout_s=60)
        reset_all_tables(cls._db)

        cls._rating_db = MySQLRatingDB(cls._db)

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
                "email": f"rating_{uniq}@example.com",
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
        price: float = 50.0,
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

    def _new_rating_for_sold_listing(self, score: int = 5) -> Rating:
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
    # CREATE / READ
    # --------------------------------------------------
    def test_add_and_get_by_id(self) -> None:
        rating = self._new_rating_for_sold_listing(score=5)

        created = self._rating_db.add(rating)

        self.assertIsNotNone(created.id)
        self.assertEqual(created.listing_id, rating.listing_id)
        self.assertEqual(created.rater_id, rating.rater_id)
        self.assertEqual(created.transaction_rating, rating.transaction_rating)

        fetched = self._rating_db.get_by_id(created.id)
        self.assertIsNotNone(fetched)
        assert fetched is not None

        self.assertEqual(fetched.id, created.id)
        self.assertEqual(fetched.listing_id, rating.listing_id)
        self.assertEqual(fetched.rater_id, rating.rater_id)
        self.assertEqual(fetched.transaction_rating, 5)

    def test_get_by_listing_id(self) -> None:
        rating = self._new_rating_for_sold_listing(score=4)
        created = self._rating_db.add(rating)

        fetched = self._rating_db.get_by_listing_id(created.listing_id)
        self.assertIsNotNone(fetched)
        assert fetched is not None

        self.assertEqual(fetched.id, created.id)
        self.assertEqual(fetched.listing_id, created.listing_id)
        self.assertEqual(fetched.rater_id, created.rater_id)

    def test_get_by_id_returns_none_when_missing(self) -> None:
        fetched = self._rating_db.get_by_id(999999)
        self.assertIsNone(fetched)

    def test_get_by_listing_id_returns_none_when_missing(self) -> None:
        fetched = self._rating_db.get_by_listing_id(999999)
        self.assertIsNone(fetched)

    def test_add_duplicate_listing_rating_raises(self) -> None:
        rating = self._new_rating_for_sold_listing(score=5)
        self._rating_db.add(rating)

        duplicate = Rating(
            listing_id=rating.listing_id,
            rater_id=rating.rater_id,
            transaction_rating=3,
        )

        with self.assertRaises(DatabaseQueryError):
            self._rating_db.add(duplicate)

    # --------------------------------------------------
    # READ LISTS
    # --------------------------------------------------
    def test_get_by_rater_id(self) -> None:
        seller_1 = self._insert_account()
        seller_2 = self._insert_account()
        buyer_id = self._insert_account()

        listing_1 = self._insert_listing(seller_1, sold_to_id=buyer_id, is_sold=True)
        listing_2 = self._insert_listing(seller_2, sold_to_id=buyer_id, is_sold=True)

        created_1 = self._rating_db.add(Rating(
            listing_id=listing_1,
            rater_id=buyer_id,
            transaction_rating=5,
        ))
        created_2 = self._rating_db.add(Rating(
            listing_id=listing_2,
            rater_id=buyer_id,
            transaction_rating=3,
        ))

        ratings = self._rating_db.get_by_rater_id(buyer_id)

        self.assertEqual(len(ratings), 2)
        ids = {r.id for r in ratings}
        self.assertEqual(ids, {created_1.id, created_2.id})

    def test_get_all(self) -> None:
        r1 = self._rating_db.add(self._new_rating_for_sold_listing(score=5))
        r2 = self._rating_db.add(self._new_rating_for_sold_listing(score=2))

        ratings = self._rating_db.get_all()

        self.assertEqual(len(ratings), 2)
        ids = [r.id for r in ratings]
        self.assertEqual(ids, [r1.id, r2.id])

    def test_get_recent_with_limit_and_offset(self) -> None:
        r1 = self._rating_db.add(self._new_rating_for_sold_listing(score=1))
        r2 = self._rating_db.add(self._new_rating_for_sold_listing(score=2))
        r3 = self._rating_db.add(self._new_rating_for_sold_listing(score=3))

        recent = self._rating_db.get_recent(limit=2, offset=0)
        self.assertEqual(len(recent), 2)
        self.assertEqual([r.id for r in recent], [r3.id, r2.id])

        recent_offset = self._rating_db.get_recent(limit=1, offset=1)
        self.assertEqual(len(recent_offset), 1)
        self.assertEqual(recent_offset[0].id, r2.id)

        _ = r1  # keeps intent explicit

    def test_get_by_score(self) -> None:
        r1 = self._rating_db.add(self._new_rating_for_sold_listing(score=5))
        self._rating_db.add(self._new_rating_for_sold_listing(score=2))
        r3 = self._rating_db.add(self._new_rating_for_sold_listing(score=5))

        ratings = self._rating_db.get_by_score(5)

        self.assertEqual(len(ratings), 2)
        ids = {r.id for r in ratings}
        self.assertEqual(ids, {r1.id, r3.id})

    # --------------------------------------------------
    # AGGREGATES
    # --------------------------------------------------
    def test_get_average_rating_by_account_id(self) -> None:
        seller_id = self._insert_account()
        buyer_1 = self._insert_account()
        buyer_2 = self._insert_account()

        listing_1 = self._insert_listing(seller_id, sold_to_id=buyer_1, is_sold=True)
        listing_2 = self._insert_listing(seller_id, sold_to_id=buyer_2, is_sold=True)

        self._rating_db.add(Rating(
            listing_id=listing_1,
            rater_id=buyer_1,
            transaction_rating=4,
        ))
        self._rating_db.add(Rating(
            listing_id=listing_2,
            rater_id=buyer_2,
            transaction_rating=2,
        ))

        avg = self._rating_db.get_average_rating_by_account_id(seller_id)
        self.assertEqual(avg, 3.0)

    def test_get_average_rating_by_account_id_returns_none_when_no_ratings(self) -> None:
        seller_id = self._insert_account()

        avg = self._rating_db.get_average_rating_by_account_id(seller_id)

        self.assertIsNone(avg)

    def test_get_sum_of_ratings_given_by_account_id(self) -> None:
        seller_1 = self._insert_account()
        seller_2 = self._insert_account()
        buyer_id = self._insert_account()

        listing_1 = self._insert_listing(seller_1, sold_to_id=buyer_id, is_sold=True)
        listing_2 = self._insert_listing(seller_2, sold_to_id=buyer_id, is_sold=True)

        self._rating_db.add(Rating(
            listing_id=listing_1,
            rater_id=buyer_id,
            transaction_rating=5,
        ))
        self._rating_db.add(Rating(
            listing_id=listing_2,
            rater_id=buyer_id,
            transaction_rating=3,
        ))

        total = self._rating_db.get_sum_of_ratings_given_by_account_id(buyer_id)
        self.assertEqual(total, 8)

    def test_get_sum_of_ratings_received_by_account_id(self) -> None:
        seller_id = self._insert_account()
        buyer_1 = self._insert_account()
        buyer_2 = self._insert_account()

        listing_1 = self._insert_listing(seller_id, sold_to_id=buyer_1, is_sold=True)
        listing_2 = self._insert_listing(seller_id, sold_to_id=buyer_2, is_sold=True)

        self._rating_db.add(Rating(
            listing_id=listing_1,
            rater_id=buyer_1,
            transaction_rating=1,
        ))
        self._rating_db.add(Rating(
            listing_id=listing_2,
            rater_id=buyer_2,
            transaction_rating=4,
        ))

        total = self._rating_db.get_sum_of_ratings_received_by_account_id(seller_id)
        self.assertEqual(total, 5)

    def test_get_average_for_rater(self) -> None:
        seller_1 = self._insert_account()
        seller_2 = self._insert_account()
        buyer_id = self._insert_account()

        listing_1 = self._insert_listing(seller_1, sold_to_id=buyer_id, is_sold=True)
        listing_2 = self._insert_listing(seller_2, sold_to_id=buyer_id, is_sold=True)

        self._rating_db.add(Rating(
            listing_id=listing_1,
            rater_id=buyer_id,
            transaction_rating=5,
        ))
        self._rating_db.add(Rating(
            listing_id=listing_2,
            rater_id=buyer_id,
            transaction_rating=1,
        ))

        avg = self._rating_db.get_average_for_rater(buyer_id)
        self.assertEqual(avg, 3.0)

    def test_get_average_for_rater_returns_none_when_no_ratings(self) -> None:
        account_id = self._insert_account()

        avg = self._rating_db.get_average_for_rater(account_id)

        self.assertIsNone(avg)

    def test_count_ratings_received_by_account_id(self) -> None:
        seller_id = self._insert_account()
        buyer_1 = self._insert_account()
        buyer_2 = self._insert_account()

        listing_1 = self._insert_listing(seller_id, sold_to_id=buyer_1, is_sold=True)
        listing_2 = self._insert_listing(seller_id, sold_to_id=buyer_2, is_sold=True)

        self._rating_db.add(Rating(
            listing_id=listing_1,
            rater_id=buyer_1,
            transaction_rating=5,
        ))
        self._rating_db.add(Rating(
            listing_id=listing_2,
            rater_id=buyer_2,
            transaction_rating=3,
        ))

        count = self._rating_db.count_ratings_received_by_account_id(seller_id)
        self.assertEqual(count, 2)

    def test_count_ratings_received_by_account_id_returns_zero_when_no_ratings(self) -> None:
        seller_id = self._insert_account()

        count = self._rating_db.count_ratings_received_by_account_id(seller_id)
        self.assertEqual(count, 0)

    def test_count_by_rater(self) -> None:
        seller_1 = self._insert_account()
        seller_2 = self._insert_account()
        buyer_id = self._insert_account()

        listing_1 = self._insert_listing(seller_1, sold_to_id=buyer_id, is_sold=True)
        listing_2 = self._insert_listing(seller_2, sold_to_id=buyer_id, is_sold=True)

        self._rating_db.add(Rating(
            listing_id=listing_1,
            rater_id=buyer_id,
            transaction_rating=5,
        ))
        self._rating_db.add(Rating(
            listing_id=listing_2,
            rater_id=buyer_id,
            transaction_rating=4,
        ))

        count = self._rating_db.count_by_rater(buyer_id)
        self.assertEqual(count, 2)

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------
    def test_update(self) -> None:
        created = self._rating_db.add(self._new_rating_for_sold_listing(score=2))

        updated_input = Rating(
            listing_id=created.listing_id,
            rater_id=created.rater_id,
            transaction_rating=5,
            rating_id=created.id,
        )

        updated = self._rating_db.update(updated_input)

        self.assertEqual(updated.id, created.id)
        self.assertEqual(updated.transaction_rating, 5)
        self.assertEqual(updated.listing_id, created.listing_id)
        self.assertEqual(updated.rater_id, created.rater_id)

    def test_update_missing_raises(self) -> None:
        missing = Rating(
            listing_id=1,
            rater_id=1,
            transaction_rating=4,
            rating_id=999999,
        )

        with self.assertRaises(RatingNotFoundError):
            self._rating_db.update(missing)

    def test_set_score(self) -> None:
        created = self._rating_db.add(self._new_rating_for_sold_listing(score=2))

        self._rating_db.set_score(created.id, 4)

        fetched = self._rating_db.get_by_id(created.id)
        self.assertIsNotNone(fetched)
        assert fetched is not None
        self.assertEqual(fetched.transaction_rating, 4)

    def test_set_score_missing_raises(self) -> None:
        with self.assertRaises(RatingNotFoundError):
            self._rating_db.set_score(999999, 4)

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------
    def test_remove(self) -> None:
        created = self._rating_db.add(self._new_rating_for_sold_listing(score=5))

        deleted = self._rating_db.remove(created.id)
        self.assertTrue(deleted)

        deleted_again = self._rating_db.remove(created.id)
        self.assertFalse(deleted_again)

    def test_remove_by_listing_id(self) -> None:
        created = self._rating_db.add(self._new_rating_for_sold_listing(score=5))

        deleted = self._rating_db.remove_by_listing_id(created.listing_id)
        self.assertTrue(deleted)

        deleted_again = self._rating_db.remove_by_listing_id(created.listing_id)
        self.assertFalse(deleted_again)