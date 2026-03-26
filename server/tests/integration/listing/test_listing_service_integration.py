from __future__ import annotations

import os
import unittest

from src.business_logic.services.listing_service import ListingService
from src.business_logic.managers.listing.listing_manager import ListingManager
from src.db.listing.mysql.mysql_listing_db import MySQLListingDB
from src.db.account.mysql.mysql_account_db import MySQLAccountDB
from src.domain_models.account import Account
from src.utils.errors import ValidationError

from tests.helpers.integration_db import ensure_tables_exist, reset_all_tables
from tests.helpers.integration_db_session import acquire, get_db, release


class _StubCommentDB:
    """
    Temporary stub while CommentDB isn't implemented.
    """

    def get_by_listing_id(self, listing_id: int):
        return []

    def add(self, *args, **kwargs):
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        raise NotImplementedError


class TestListingServiceIntegration(unittest.TestCase):
    """
    Integration tests:
      ListingService -> ListingManager -> MySQLListingDB -> real MySQL (docker)
    """

    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SECRET_KEY", "test-secret")

        cls._session = acquire(timeout_s=120)
        cls._db = get_db()

        ensure_tables_exist(cls._db, timeout_s=60)
        reset_all_tables(cls._db)

        cls._account_db = MySQLAccountDB(db=cls._db)
        cls._listing_db = MySQLListingDB(db=cls._db)
        cls._comment_db = _StubCommentDB()
        cls._manager = ListingManager(
            listing_db=cls._listing_db,
            comment_db=cls._comment_db,
        )
        cls._service = ListingService(cls._manager)

    @classmethod
    def tearDownClass(cls) -> None:
        release(cls._session, remove_volumes=False)

    def setUp(self) -> None:
        reset_all_tables(self._db)

    def _create_account(self, email: str) -> int:
        created = self._account_db.add(
            Account(
                email=email,
                password="Password1",
                fname="Test",
                lname="User",
            )
        )
        return created.id

    # -----------------------------
    # get_all_listing
    # -----------------------------
    def test_get_all_listing_empty_returns_empty_list(self) -> None:
        listings = self._service.get_all_listing()
        self.assertIsInstance(listings, list)
        self.assertEqual(listings, [])

    # -----------------------------
    # create_listing
    # -----------------------------
    def test_create_listing_persists_and_returns_id(self) -> None:
        seller_id = self._create_account("seller1@umanitoba.ca")

        created = self._service.create_listing(
            seller_id=seller_id,
            title="Bike",
            description="Good condition",
            price=50.0,
            location="Winnipeg",
            image_url=None,
        )

        listing_id = getattr(created, "id", None)
        self.assertIsNotNone(listing_id)

        all_listings = self._listing_db.get_all()
        self.assertEqual(len(all_listings), 1)
        self.assertEqual(all_listings[0].title, "Bike")
        self.assertEqual(all_listings[0].seller_id, seller_id)
        self.assertEqual(all_listings[0].price, 50.0)
        self.assertIsNone(all_listings[0].image_url)

    def test_create_listing_image_key_valid_persists(self) -> None:
        seller_id = self._create_account("seller2@umanitoba.ca")

        created = self._service.create_listing(
            seller_id=seller_id,
            title="Laptop",
            description="Works",
            price=500.0,
            location="Winnipeg",
            image_url="listings/img.jpg",
        )

        listing_id = getattr(created, "id", None)
        self.assertIsNotNone(listing_id)

        in_db = self._listing_db.get_all()[0]
        self.assertEqual(in_db.image_url, "listings/img.jpg")

    # -----------------------------
    # create_listing validation errors
    # -----------------------------
    def test_create_listing_rejects_empty_title(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self._service.create_listing(
                seller_id=1,
                title="   ",
                description="desc",
                price=10.0,
                location="Winnipeg",
                image_url=None,
            )

        self.assertIn("errors", ctx.exception.details)
        self.assertIn("title", ctx.exception.details["errors"])

    def test_create_listing_rejects_empty_description(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self._service.create_listing(
                seller_id=1,
                title="A",
                description="",
                price=10.0,
                location="Winnipeg",
                image_url=None,
            )

        self.assertIn("description", ctx.exception.details["errors"])

    def test_create_listing_rejects_price_none(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self._service.create_listing(
                seller_id=1,
                title="A",
                description="B",
                price=None,
                location="Winnipeg",
                image_url=None,
            )

        self.assertIn("price", ctx.exception.details["errors"])

    def test_create_listing_rejects_price_zero_or_negative(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self._service.create_listing(
                seller_id=1,
                title="A",
                description="B",
                price=0.0,
                location="Winnipeg",
                image_url=None,
            )

        self.assertIn("price", ctx.exception.details["errors"])

        with self.assertRaises(ValidationError) as ctx2:
            self._service.create_listing(
                seller_id=1,
                title="A",
                description="B",
                price=-1.0,
                location="Winnipeg",
                image_url=None,
            )

        self.assertIn("price", ctx2.exception.details["errors"])

    def test_create_listing_rejects_empty_location(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self._service.create_listing(
                seller_id=1,
                title="A",
                description="B",
                price=10.0,
                location="",
                image_url=None,
            )

        self.assertIn("location", ctx.exception.details["errors"])

    def test_create_listing_rejects_image_key_empty_string(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self._service.create_listing(
                seller_id=1,
                title="A",
                description="B",
                price=10.0,
                location="Winnipeg",
                image_url="   ",
            )

        self.assertIn("image_url", ctx.exception.details["errors"])

    def test_create_listing_rejects_image_key_starting_with_slash(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            self._service.create_listing(
                seller_id=1,
                title="A",
                description="B",
                price=10.0,
                location="Winnipeg",
                image_url="/listings/img.jpg",
            )

        self.assertIn("image_url", ctx.exception.details["errors"])

    # -----------------------------
    # get_listing_by_user_id
    # -----------------------------
    def test_get_listing_by_user_id_returns_only_that_sellers_listings(self) -> None:
        seller1 = self._create_account("s1@umanitoba.ca")
        seller2 = self._create_account("s2@umanitoba.ca")

        self._service.create_listing(seller1, "A1", "D", 10.0, "Winnipeg", None)
        self._service.create_listing(seller1, "A2", "D", 12.0, "Winnipeg", None)
        self._service.create_listing(seller2, "B1", "D", 99.0, "Winnipeg", None)

        seller_1_listings = self._service.get_listing_by_user_id(seller1)
        self.assertEqual(len(seller_1_listings), 2)
        self.assertTrue(all(l.seller_id == seller1 for l in seller_1_listings))

        seller_2_listings = self._service.get_listing_by_user_id(seller2)
        self.assertEqual(len(seller_2_listings), 1)
        self.assertEqual(seller_2_listings[0].seller_id, seller2)
        self.assertEqual(seller_2_listings[0].title, "B1")