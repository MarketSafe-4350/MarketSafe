import unittest
from types import SimpleNamespace
from datetime import datetime, timezone
from unittest.mock import MagicMock

from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from src.api.routes import listing_routes
from src.auth.dependencies import get_current_user_id

from src.api.dependencies import get_listing_service, get_comment_service
from src.utils.errors import (
    ValidationError,
    DatabaseUnavailableError,
)

from src.api.errors.exception_handlers import AppError, app_error_handler


class TestListingRouteIntegration(unittest.TestCase):
    """
    Route tests (with mocked service):
    route -> Depends(get_listing_service) -> service mock
    Includes error-path tests to verify exception handling.
    """

    def setUp(self) -> None:
        self.app = FastAPI()
        self.app.include_router(listing_routes.router)
        self.app.add_exception_handler(AppError, app_error_handler)

        def fake_auth_user_id() -> int:
            return 999

        self.app.dependency_overrides[get_current_user_id] = fake_auth_user_id

        self.mock_listing_service = MagicMock()
        self.mock_comment_service = MagicMock()

        # default service override
        self.app.dependency_overrides[get_comment_service] = (
            lambda: self.mock_comment_service
        )

        self.app.dependency_overrides[get_listing_service] = (
            lambda: self.mock_listing_service
        )

        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    # ---------- happy paths ---------- #

    def test_get_all_listing_returns_list(self) -> None:
        created_at = datetime(2026, 2, 22, tzinfo=timezone.utc)

        self.mock_listing_service.get_all_listing.return_value = [
            SimpleNamespace(
                id=1,
                seller_id=999,
                title="T1",
                description="D1",
                price=10.0,
                location="Winnipeg",
                image_url=None,
                created_at=created_at,
                is_sold=False,
            )
        ]

        resp = self.client.get("/listings")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[0]["seller_id"], 999)
        self.assertEqual(data[0]["created_at"], created_at.isoformat())

        self.mock_listing_service.get_all_listing.assert_called_once()

    def test_get_my_listing_returns_list(self) -> None:
        self.mock_listing_service.get_listing_by_user_id.return_value = [
            SimpleNamespace(
                id=2,
                seller_id=999,
                title="Mine",
                description="My desc",
                price=99.99,
                location="Winnipeg",
                image_url=None,
                created_at=None,
                is_sold=False,
            )
        ]

        resp = self.client.get("/listings/me")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(data[0]["id"], 2)
        self.assertEqual(data[0]["seller_id"], 999)

        self.mock_listing_service.get_listing_by_user_id.assert_called_once_with(
            user_id=999
        )

    def test_create_listing_returns_created_listing(self) -> None:
        created_at = datetime(2026, 2, 22, tzinfo=timezone.utc)

        self.mock_listing_service.create_listing.return_value = SimpleNamespace(
            id=3,
            seller_id=999,
            title="A",
            description="B",
            price=10.0,
            location="Winnipeg",
            image_url="http://example.com/image.jpg",
            created_at=created_at,
            is_sold=False,
        )

        payload = {
            "title": "A",
            "description": "B",
            "price": 10.0,
            "location": "Winnipeg",
            "image_url": "http://example.com/image.jpg",
        }

        resp = self.client.post("/listings", json=payload)
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(data["id"], 3)
        self.assertEqual(data["seller_id"], 999)

        self.mock_listing_service.create_listing.assert_called_once_with(
            seller_id=999,
            title="A",
            description="B",
            price=10.0,
            location="Winnipeg",
            image_url="http://example.com/image.jpg",
        )

    # ---------- listing routes errors ---------- #

    def test_create_listing_validation_error_returns_422(self) -> None:
        """
        Service raises ValidationError -> should return 422 (via AppError handler)
        """
        self.mock_listing_service.create_listing.side_effect = ValidationError(
            message="Validation failed for listing creation.",
            details={"errors": {"price": ["Price must be a non-negative number."]}},
        )

        payload = {
            "title": "A",
            "description": "B",
            "price": -10.0,  # invalid
            "location": "Winnipeg",
            "image_url": None,
        }

        resp = self.client.post("/listings", json=payload)
        self.assertEqual(resp.status_code, 422)

        body = resp.json()
        self.assertIn("error_message", body)

    def test_get_all_listing_db_unavailable_returns_503(self) -> None:
        """
        Service raises DatabaseUnavailableError -> should return 503
        """
        self.mock_listing_service.get_all_listing.side_effect = (
            DatabaseUnavailableError("DB down")
        )

        resp = self.client.get("/listings")
        self.assertEqual(resp.status_code, 503)

        body = resp.json()
        self.assertIn("error_message", body)

    def test_get_all_listing_unauthorized_returns_401(self) -> None:
        """
        Auth dependency fails -> should return 401
        """

        def fake_unauthorized() -> int:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        self.app.dependency_overrides[get_current_user_id] = fake_unauthorized

        resp = self.client.get("/listings")
        self.assertEqual(resp.status_code, 401)

    def test_get_listing_comments_returns_list(self) -> None:
        listing_id = 123
        created = datetime(2026, 2, 22, tzinfo=timezone.utc)

        self.mock_comment_service.get_all_comments_listing.return_value = [
            SimpleNamespace(
                id=1,
                listing_id=listing_id,
                author_id=999,
                body="First!",
                created_date=created,
            ),
            SimpleNamespace(
                id=2,
                listing_id=listing_id,
                author_id=888,
                body="Still available?",
                created_date=None,
            ),
        ]

        resp = self.client.get(f"/listings/{listing_id}/comments")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[0]["listing_id"], listing_id)
        self.assertEqual(data[0]["author_id"], 999)
        self.assertEqual(data[0]["body"], "First!")
        self.assertEqual(data[0]["created_date"], created.isoformat())

        self.assertEqual(data[1]["id"], 2)
        self.assertEqual(data[1]["created_date"], None)

        self.mock_comment_service.get_all_comments_listing.assert_called_once_with(
            listing_id=listing_id
        )

    def test_create_listing_comment_returns_created_comment(self) -> None:
        listing_id = 123
        created = datetime(2026, 2, 22, tzinfo=timezone.utc)

        # what the service returns (domain-like object)
        self.mock_comment_service.create_comment.return_value = SimpleNamespace(
            id=10,
            listing_id=listing_id,
            author_id=999,
            body="Is it still available?",
            created_date=created,
        )

        payload = {"body": "Is it still available?"}

        resp = self.client.post(f"/listings/{listing_id}/comments", json=payload)
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(data["id"], 10)
        self.assertEqual(data["listing_id"], listing_id)
        self.assertEqual(data["author_id"], 999)
        self.assertEqual(data["body"], "Is it still available?")
        self.assertEqual(data["created_date"], created.isoformat())

        args, kwargs = self.mock_comment_service.create_comment.call_args
        self.assertEqual(kwargs["actor_id"], 999)
        self.assertEqual(kwargs["listing_id"], listing_id)

        sent_comment = kwargs["comment"]
        self.assertEqual(sent_comment.listing_id, listing_id)
        self.assertEqual(sent_comment.author_id, 999)
        self.assertEqual(sent_comment.body, payload["body"])
