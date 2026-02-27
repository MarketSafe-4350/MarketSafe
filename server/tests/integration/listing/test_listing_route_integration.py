import unittest
from types import SimpleNamespace
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from src.api.routes import listing_routes
from src.auth.dependencies import get_current_user_id

from src.utils.errors import (
    ValidationError,
    DatabaseUnavailableError,
    DatabaseQueryError,
)

from src.api.errors.exception_handlers import AppError, app_error_handler


class TestListingRouteIntegration(unittest.TestCase):
    """
    Route tests (with mocked service): route -> service -> manager -> db (docker)
    Includes error-path tests to verify exception handling.
    """

    def setUp(self) -> None:
        self.app = FastAPI()
        self.app.include_router(listing_routes.router)

        self.app.add_exception_handler(AppError, app_error_handler)

        def fake_auth_user_id() -> int:
            return 999

        self.app.dependency_overrides[get_current_user_id] = fake_auth_user_id
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    # ---------- happy paths ---------- #

    @patch("src.api.routes.listing_routes._get_service")
    def test_get_all_listing_returns_list(self, mock_get_service: MagicMock) -> None:
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        created_at = datetime(2026, 2, 22, tzinfo=timezone.utc)
        mock_service.get_all_listing.return_value = [
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

    @patch("src.api.routes.listing_routes._get_service")
    def test_get_my_listing_returns_list(self, mock_get_service: MagicMock) -> None:
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.get_listing_by_user_id.return_value = [
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

        mock_service.get_listing_by_user_id.assert_called_once_with(user_id=999)

    @patch("src.api.routes.listing_routes._get_service")
    def test_search_listings_returns_matching_results(
        self, mock_get_service: MagicMock
    ) -> None:
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        created_at = datetime(2026, 2, 25, tzinfo=timezone.utc)
        mock_service.search_listings.return_value = [
            SimpleNamespace(
                id=20,
                seller_id=12,
                title="Gaming Laptop",
                description="RTX laptop",
                price=850.0,
                location="Winnipeg",
                image_url=None,
                created_at=created_at,
                is_sold=False,
            )
        ]

        resp = self.client.get("/listings/search", params={"q": "laptop gaming"})
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Gaming Laptop")
        mock_service.search_listings.assert_called_once_with(query="laptop gaming")

    def test_search_listings_missing_query_returns_422(self) -> None:
        resp = self.client.get("/listings/search")
        self.assertEqual(resp.status_code, 422)

    @patch("src.api.routes.listing_routes._get_service")
    def test_create_listing_returns_created_listing(
        self, mock_get_service: MagicMock
    ) -> None:
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        created_at = datetime(2026, 2, 22, tzinfo=timezone.utc)
        mock_service.create_listing.return_value = SimpleNamespace(
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

        mock_service.create_listing.assert_called_once_with(
            seller_id=999,
            title="A",
            description="B",
            price=10.0,
            location="Winnipeg",
            image_url="http://example.com/image.jpg",
        )

    # ---------- listing routes errors ---------- #

    @patch("src.api.routes.listing_routes._get_service")
    def test_create_listing_validation_error_returns_422(
        self, mock_get_service: MagicMock
    ) -> None:
        """
        Service raises ValidationError -> should return 422
        """
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.create_listing.side_effect = ValidationError(
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

    @patch("src.api.routes.listing_routes._get_service")
    def test_get_all_listing_db_unavailable_returns_503(
        self, mock_get_service: MagicMock
    ) -> None:
        """
        Service raises DatabaseUnavailableError -> should return 503
        """
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.get_all_listing.side_effect = DatabaseUnavailableError("DB down")

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
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        self.app.dependency_overrides[get_current_user_id] = fake_unauthorized

        resp = self.client.get("/listings")
        self.assertEqual(resp.status_code, 401)
