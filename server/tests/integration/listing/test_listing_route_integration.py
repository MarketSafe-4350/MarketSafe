from __future__ import annotations

import os
import unittest

from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from src.api.routes import listing_routes
from src.auth.dependencies import get_current_user_id
from src.api.dependencies import get_listing_service, get_comment_service
from src.api.errors.exception_handlers import AppError, app_error_handler

from src.business_logic.services.listing_service import ListingService
from src.business_logic.services.comment_service import CommentService

from src.business_logic.managers.listing.listing_manager import ListingManager
from src.business_logic.managers.comment.comment_manager import CommentManager
from src.business_logic.managers.account.account_manager import AccountManager

from src.db.listing.mysql.mysql_listing_db import MySQLListingDB
from src.db.comment.mysql.mysql_comment_db import MySQLCommentDB
from src.db.account.mysql.mysql_account_db import MySQLAccountDB

from src.domain_models.account import Account
from src.domain_models.listing import Listing
from src.domain_models.comment import Comment

from tests.helpers.integration_db import ensure_tables_exist, reset_all_tables
from tests.helpers.integration_db_session import acquire, get_db, release


class TestListingRouteIntegration(unittest.TestCase):
    """
    integration tests (MySQL docker):
       TestClient -> router -> real services -> real managers -> MySQL DB
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
        cls._comment_db = MySQLCommentDB(db=cls._db)

        try:
            cls._account_manager = AccountManager(
                account_db=cls._account_db, listing_db=cls._listing_db
            )
        except TypeError:
            cls._account_manager = AccountManager(account_db=cls._account_db)

        cls._listing_manager = ListingManager(
            listing_db=cls._listing_db,
            comment_db=cls._comment_db,
        )
        cls._comment_manager = CommentManager(comment_db=cls._comment_db)

        cls._listing_service = ListingService(listing_manager=cls._listing_manager)
        cls._comment_service = CommentService(
            comment_manager=cls._comment_manager,
            listing_manager=cls._listing_manager,
            account_manager=cls._account_manager,
        )

        cls.app = FastAPI()
        cls.app.include_router(listing_routes.router)
        cls.app.add_exception_handler(AppError, app_error_handler)

        cls.app.dependency_overrides[get_listing_service] = lambda: cls._listing_service
        cls.app.dependency_overrides[get_comment_service] = lambda: cls._comment_service

        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.app.dependency_overrides.clear()
        release(cls._session, remove_volumes=False)

    def setUp(self) -> None:
        reset_all_tables(self._db)

        self.user_id = self._create_account(
            email="user@umanitoba.ca",
            fname="Test",
            lname="User",
            verified=True,
        )
        self.app.dependency_overrides[get_current_user_id] = lambda: self.user_id

    def tearDown(self) -> None:
        self.app.dependency_overrides.pop(get_current_user_id, None)

    # -----------------------------
    # helpers
    # -----------------------------
    def _create_account(
        self,
        *,
        email: str,
        fname: str,
        lname: str,
        verified: bool,
    ) -> int:
        created = self._account_db.add(
            Account(
                email=email,
                password="Password1",
                fname=fname,
                lname=lname,
                verified=verified,
            )
        )
        return created.id

    def _create_listing(self, *, seller_id: int, title: str) -> int:
        """
        IMPORTANT:
        Your ListingManager.create_listing expects a Listing domain object:
            def create_listing(self, listing: Listing) -> Listing
        So in tests we construct Listing and pass it in.
        """
        created = self._listing_manager.create_listing(
            Listing(
                seller_id=seller_id,
                title=title,
                description="Desc",
                price=10.0,
                location="Winnipeg",
                image_url=None,
            )
        )
        return created.id

    # ---------- happy paths ---------- #

    def test_get_all_listing_returns_list(self) -> None:
        # seed one listing
        self._create_listing(seller_id=self.user_id, title="T1")

        resp = self.client.get("/listings")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

        self.assertEqual(data[0]["seller_id"], self.user_id)
        self.assertEqual(data[0]["title"], "T1")
        self.assertIn("created_at", data[0])

    def test_get_my_listing_returns_list(self) -> None:
        # seed listings for current user + another user
        self._create_listing(seller_id=self.user_id, title="Mine1")

        other_id = self._create_account(
            email="other@umanitoba.ca",
            fname="Other",
            lname="User",
            verified=True,
        )
        self._create_listing(seller_id=other_id, title="NotMine")

        resp = self.client.get("/listings/me")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["seller_id"], self.user_id)
        self.assertEqual(data[0]["title"], "Mine1")

    def test_create_listing_returns_created_listing(self) -> None:
        payload = {
            "title": "A",
            "description": "B",
            "price": 10.0,
            "location": "Winnipeg",
            "image_url": None,
        }

        resp = self.client.post("/listings", json=payload)
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsNotNone(data["id"])
        self.assertEqual(data["seller_id"], self.user_id)
        self.assertEqual(data["title"], "A")
        self.assertEqual(data["price"], 10.0)

    def test_get_listing_comments_returns_list(self) -> None:
        listing_id = self._create_listing(seller_id=self.user_id, title="WithComments")

        # create another verified user to comment too
        user2_id = self._create_account(
            email="u2@umanitoba.ca",
            fname="Alice",
            lname="One",
            verified=True,
        )

        self._comment_service.create_comment(
            actor_id=self.user_id,
            listing_id=listing_id,
            comment=Comment(
                listing_id=listing_id, author_id=self.user_id, body="First!"
            ),
        )
        self._comment_service.create_comment(
            actor_id=user2_id,
            listing_id=listing_id,
            comment=Comment(
                listing_id=listing_id, author_id=user2_id, body="Still available?"
            ),
        )

        resp = self.client.get(f"/listings/{listing_id}/comments")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

        bodies = {c["body"] for c in data}
        self.assertEqual(bodies, {"First!", "Still available?"})

        for item in data:
            self.assertIn("author_name", item)
            self.assertIn("created_date", item)

    def test_create_listing_comment_returns_created_comment(self) -> None:
        listing_id = self._create_listing(seller_id=self.user_id, title="CommentHere")

        payload = {"body": "Is it still available?"}

        resp = self.client.post(f"/listings/{listing_id}/comments", json=payload)
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsNotNone(data["id"])
        self.assertEqual(data["listing_id"], listing_id)
        self.assertEqual(data["author_id"], self.user_id)
        self.assertEqual(data["body"], payload["body"])

        self.assertIn("author_name", data)
        self.assertIn("created_date", data)

    # ---------- error paths ---------- #

    def test_create_listing_validation_error_returns_422(self) -> None:
        payload = {
            "title": "A",
            "description": "B",
            "price": -10.0,
            "location": "Winnipeg",
            "image_url": None,
        }

        resp = self.client.post("/listings", json=payload)
        self.assertEqual(resp.status_code, 422)

        body = resp.json()
        self.assertIn("error_message", body)

    def test_get_all_listing_unauthorized_returns_401(self) -> None:
        def fake_unauthorized() -> int:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        self.app.dependency_overrides[get_current_user_id] = fake_unauthorized

        resp = self.client.get("/listings")
        self.assertEqual(resp.status_code, 401)
