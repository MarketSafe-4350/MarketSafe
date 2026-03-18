from __future__ import annotations

import os
import unittest

from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from src.api.dependencies import (
    get_comment_service,
    get_listing_service,
    get_media_storage,
)
from src.api.errors.exception_handlers import (
    AppError,
    app_error_handler,
    request_validation_error_handler,
)
from src.api.routes import listing_routes
from src.auth.dependencies import get_current_user_id

from src.business_logic.managers.account.account_manager import AccountManager
from src.business_logic.managers.comment.comment_manager import CommentManager
from src.business_logic.managers.listing.listing_manager import ListingManager
from src.business_logic.services.comment_service import CommentService
from src.business_logic.services.listing_service import ListingService

from src.db.account.mysql.mysql_account_db import MySQLAccountDB
from src.db.comment.mysql.mysql_comment_db import MySQLCommentDB
from src.db.listing.mysql.mysql_listing_db import MySQLListingDB

from src.domain_models.account import Account
from src.domain_models.comment import Comment
from src.domain_models.listing import Listing

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
                account_db=cls._account_db,
                listing_db=cls._listing_db,
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

        cls._media_storage = cls._build_fake_media_storage()

        cls.app = FastAPI()
        cls.app.include_router(listing_routes.router)
        cls.app.add_exception_handler(AppError, app_error_handler)
        cls.app.add_exception_handler(
            RequestValidationError,
            request_validation_error_handler,
        )

        cls.app.dependency_overrides[get_listing_service] = lambda: cls._listing_service
        cls.app.dependency_overrides[get_comment_service] = lambda: cls._comment_service
        cls.app.dependency_overrides[get_media_storage] = lambda: cls._media_storage

        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.app.dependency_overrides.clear()
        release(cls._session, remove_volumes=False)

    @classmethod
    def _build_fake_media_storage(cls):
        class FakeMediaStorage:
            def public_url(self, key: str | None):
                if key is None:
                    return None
                return f"https://example.test/{key}"

            def upload_bytes(self, key: str, data: bytes, content_type: str):
                return key

        return FakeMediaStorage()

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

    def _create_listing(
        self,
        *,
        seller_id: int,
        title: str,
        image_url: str | None = None,
    ) -> int:
        created = self._listing_manager.create_listing(
            Listing(
                seller_id=seller_id,
                title=title,
                description="Desc",
                price=10.0,
                location="Winnipeg",
                image_url=image_url,
            )
        )
        return created.id

    # ---------- happy paths ---------- #

    def test_get_all_listing_returns_list(self) -> None:
        self._create_listing(
            seller_id=self.user_id,
            title="T1",
            image_url="listings/t1.jpg",
        )

        resp = self.client.get("/listings")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

        self.assertEqual(data[0]["seller_id"], self.user_id)
        self.assertEqual(data[0]["title"], "T1")
        self.assertIn("created_at", data[0])
        self.assertEqual(
            data[0]["image_url"],
            "https://example.test/listings/t1.jpg",
        )

    def test_get_my_listing_returns_list(self) -> None:
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

    def test_search_listings_returns_matching_results(self) -> None:
        self._create_listing(seller_id=self.user_id, title="Gaming Laptop")
        self._create_listing(seller_id=self.user_id, title="Desk Chair")
        self._create_listing(seller_id=self.user_id, title="Laptop Stand")

        resp = self.client.get("/listings/search", params={"q": "laptop"})
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

        titles = [item["title"] for item in data]
        self.assertTrue(any("laptop" in t.lower() for t in titles))

    def test_create_listing_returns_created_listing(self) -> None:
        payload = {
            "title": "A",
            "description": "B",
            "price": 10.0,
            "location": "Winnipeg",
            "image_url": "listings/a.jpg",
        }

        resp = self.client.post("/listings", json=payload)
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsNotNone(data.get("id"))
        self.assertEqual(data["seller_id"], self.user_id)
        self.assertEqual(data["title"], "A")
        self.assertEqual(data["description"], "B")
        self.assertEqual(data["price"], 10.0)
        self.assertEqual(data["location"], "Winnipeg")
        self.assertEqual(
            data["image_url"],
            "https://example.test/listings/a.jpg",
        )

    def test_create_listing_returns_created_listing_with_no_image(self) -> None:
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
        self.assertIsNotNone(data.get("id"))
        self.assertEqual(data["seller_id"], self.user_id)
        self.assertIsNone(data["image_url"])

    def test_get_listing_comments_returns_list(self) -> None:
        listing_id = self._create_listing(seller_id=self.user_id, title="WithComments")

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
                listing_id=listing_id,
                author_id=self.user_id,
                body="First!",
            ),
        )
        self._comment_service.create_comment(
            actor_id=user2_id,
            listing_id=listing_id,
            comment=Comment(
                listing_id=listing_id,
                author_id=user2_id,
                body="Still available?",
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

    def test_delete_listing_returns_204(self) -> None:
        listing_id = self._create_listing(seller_id=self.user_id, title="Delete Me")

        resp = self.client.delete(f"/listings/{listing_id}")
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, b"")

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

    def test_create_listing_invalid_image_key_returns_422(self) -> None:
        payload = {
            "title": "A",
            "description": "B",
            "price": 10.0,
            "location": "Winnipeg",
            "image_url": "/bad-key",
        }

        resp = self.client.post("/listings", json=payload)
        self.assertEqual(resp.status_code, 422)

        body = resp.json()
        self.assertIn("error_message", body)

    def test_get_all_listing_unauthorized_returns_401(self) -> None:
        def fake_unauthorized() -> int:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid auth_token",
            )

        self.app.dependency_overrides[get_current_user_id] = fake_unauthorized

        resp = self.client.get("/listings")
        self.assertEqual(resp.status_code, 401)

    def test_delete_listing_wrong_actor_returns_app_error(self) -> None:
        listing_id = self._create_listing(seller_id=self.user_id, title="Protected")

        other_id = self._create_account(
            email="other2@umanitoba.ca",
            fname="Other",
            lname="Two",
            verified=True,
        )
        self.app.dependency_overrides[get_current_user_id] = lambda: other_id

        resp = self.client.delete(f"/listings/{listing_id}")
        self.assertNotEqual(resp.status_code, 204)