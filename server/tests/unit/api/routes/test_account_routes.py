from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.api.routes.account_routes as account_routes

from src.api.dependencies import get_account_service
from src.auth.dependencies import get_current_user_id


class TestAccountRoutes(unittest.TestCase):
    def setUp(self) -> None:
        self.app = FastAPI()
        self.app.include_router(account_routes.router)

        self.user_id = 123
        self.app.dependency_overrides[get_current_user_id] = lambda: self.user_id

        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    # -----------------------------
    # POST /accounts  (create_account)
    # -----------------------------
    def test_create_account_success_returns_signup_response(self) -> None:
        service = MagicMock(name="account_service")

        account = MagicMock()
        account.email = "a@b.com"
        account.fname = "A"
        account.lname = "B"
        service.create_account.return_value = account
        service.generate_and_store_verification_token.return_value = (
            "rawtoken_1234567890"
        )

        self.app.dependency_overrides[get_account_service] = lambda: service
        with patch.object(account_routes, "FRONTEND_URL", "http://frontend"):
            resp = self.client.post(
                "/accounts",
                json={"email": "a@b.com", "password": "pw", "fname": "A", "lname": "B"},
            )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["email"], "a@b.com")
        self.assertEqual(data["fname"], "A")
        self.assertEqual(data["lname"], "B")
        self.assertEqual(
            data["verification_link"],
            "http://frontend/verify-email?auth_token=rawtoken_1234567890",
        )

        service.create_account.assert_called_once_with(
            email="a@b.com",
            password="pw",
            fname="A",
            lname="B",
        )
        service.generate_and_store_verification_token.assert_called_once_with(
            account_id=1
        )

    def test_create_account_exception_returns_500(self) -> None:
        service = MagicMock(name="account_service")
        service.create_account.side_effect = Exception("boom")

        self.app.dependency_overrides[get_account_service] = lambda: service
        resp = self.client.post(
            "/accounts",
            json={"email": "a@b.com", "password": "pw", "fname": "A", "lname": "B"},
        )

        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.json()["error_message"], "boom")

    # -----------------------------
    # POST /accounts/login  (login_account)
    # -----------------------------
    def test_login_account_returns_token(self) -> None:
        service = MagicMock(name="account_service")
        service.login.return_value = "jwt123"

        self.app.dependency_overrides[get_account_service] = lambda: service
        resp = self.client.post(
            "/accounts/login",
            json={"email": "a@b.com", "password": "pw"},
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json(), {"access_token": "jwt123", "token_type": "bearer"}
        )
        service.login.assert_called_once_with("a@b.com", "pw")

    # -----------------------------
    # GET /accounts/me  (get_account)
    # -----------------------------
    def test_get_account_me_returns_account_response(self) -> None:
        service = MagicMock(name="account_service")

        account = MagicMock()
        account.email = "me@b.com"
        account.fname = "Me"
        account.lname = "User"
        service.get_account_userid.return_value = account

        self.app.dependency_overrides[get_account_service] = lambda: service
        resp = self.client.get("/accounts/me")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json(), {"email": "me@b.com", "fname": "Me", "lname": "User"}
        )
        service.get_account_userid.assert_called_once_with(self.user_id)

    # -----------------------------
    # GET /accounts/verify-email  (verify_email)
    # -----------------------------
    def test_verify_email_returns_400_when_missing_token(self) -> None:
        service = MagicMock(name="account_service")

        self.app.dependency_overrides[get_account_service] = lambda: service
        resp = self.client.get("/accounts/verify-email")

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()["error_message"], "No verification auth_token provided."
        )
        service.verify_email_token.assert_not_called()

    def test_verify_email_success_uses_auth_token_param(self) -> None:
        service = MagicMock(name="account_service")

        account = MagicMock()
        account.email = "a@b.com"
        account.fname = "A"
        account.lname = "B"
        account.verified = True
        service.verify_email_token.return_value = account

        self.app.dependency_overrides[get_account_service] = lambda: service
        resp = self.client.get("/accounts/verify-email?auth_token=auth_token_1234567890")

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["email"], "a@b.com")
        self.assertEqual(data["verified"], True)
        self.assertEqual(data["message"], "Email verified successfully!")
        service.verify_email_token.assert_called_once_with("auth_token_1234567890")

    def test_verify_email_success_uses_legacy_token_param_when_auth_token_missing(
        self,
    ) -> None:
        service = MagicMock(name="account_service")

        account = MagicMock()
        account.email = "a@b.com"
        account.fname = "A"
        account.lname = "B"
        account.verified = True
        service.verify_email_token.return_value = account

        self.app.dependency_overrides[get_account_service] = lambda: service
        resp = self.client.get("/accounts/verify-email?token=legacy_1234567890")

        self.assertEqual(resp.status_code, 200)
        service.verify_email_token.assert_called_once_with("legacy_1234567890")

    def test_verify_email_known_error_returns_error_status_code(self) -> None:
        service = MagicMock(name="account_service")

        class FakeTokenErr(Exception):
            def __init__(self, message: str, status_code: int):
                super().__init__(message)
                self.message = message
                self.status_code = status_code

        self.app.dependency_overrides[get_account_service] = lambda: service
        service.verify_email_token.side_effect = FakeTokenErr("nope", 404)

        with patch.object(account_routes, "TokenNotFoundError", FakeTokenErr):
            resp = self.client.get(
                "/accounts/verify-email?auth_token=auth_token_1234567890"
            )

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["error_message"], "nope")

    def test_verify_email_unexpected_error_returns_500(self) -> None:
        service = MagicMock(name="account_service")
        service.verify_email_token.side_effect = Exception("unexpected")

        self.app.dependency_overrides[get_account_service] = lambda: service
        resp = self.client.get("/accounts/verify-email?auth_token=auth_token_1234567890")

        self.assertEqual(resp.status_code, 500)
        self.assertEqual(
            resp.json()["error_message"], "An error occurred during verification"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
