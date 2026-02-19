from __future__ import annotations

import unittest
from unittest.mock import MagicMock


from src.business_logic.services.account_service import AccountService
from src.domain_models import Account

from src.utils import ValidationError, DatabaseUnavailableError, AccountAlreadyExistsError, AppError
from src.api.errors import ApiError


class TestAccountService(unittest.TestCase):
    def setUp(self) -> None:
        # account_manager is a dependency of AccountService
        self.manager: MagicMock = MagicMock()
        self.service = AccountService(self.manager)

    # -----------------------------
    # create_account - happy path
    # -----------------------------
    def test_create_account_success_delegates_to_manager(self) -> None:
        created = Account(
            account_id=123,
            email="test@umanitoba.ca",
            password="Password1",
            fname="John",
            lname="Smith",
            verified=False,
        )

        self.manager.create_account.return_value = created

        out = self.service.create_account(
            email="test@umanitoba.ca",
            password="Password1",
            fname="John",
            lname="Smith",
        )

        self.assertEqual(out, created)
        self.manager.create_account.assert_called_once()
        passed_account: Account = self.manager.create_account.call_args[0][0]
        self.assertEqual(passed_account.email, "test@umanitoba.ca")

    # -----------------------------
    # validate_account - email domain
    # -----------------------------
    def test_create_account_rejects_non_umanitoba_domain(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.create_account(
                email="test@gmail.com",
                password="Password1",
                fname="John",
                lname="Smith",
            )

        self.manager.create_account.assert_not_called()

    # -----------------------------
    # validate_account - password strength
    # -----------------------------
    def test_create_account_rejects_weak_password(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.create_account(
                email="test1@umanitoba.ca",
                password="password",  # missing uppercase and number
                fname="John",
                lname="Smith",
            )

        self.manager.create_account.assert_not_called()

    # -----------------------------
    # create_account - duplicate email mapping
    # -----------------------------
    def test_create_account_duplicate_email_raises_accountalreadyexists(self):
            self.manager.create_account.side_effect = AccountAlreadyExistsError(
                message="Account already exists",
                details={"email": "dup@umanitoba.ca"},
            )

            with self.assertRaises(AccountAlreadyExistsError):
                self.service.create_account(
                    email="dup@umanitoba.ca",
                    password="Password1",
                    fname="A",
                    lname="B",
                )

    # -----------------------------
    # create_account - db unavailable mapping
    # -----------------------------

    # def test_create_account_db_unavailable_maps_to_503(self) -> None:
    #     self.manager.create_account.side_effect = DatabaseUnavailableError(
    #         message="Database is unavailable."
    #     )

    #     with self.assertRaises(DatabaseUnavailableError) as ctx:
    #         self.service.create_account(
    #             email="test@umanitoba.ca",
    #             password="Password1",
    #             fname="John",
    #             lname="Smith",
    #         )

    #     self.assertEqual(ctx.exception.status_code, 503)
    def test_create_account_db_unavailable_maps_to_503(self) -> None:
        self.manager.create_account.side_effect = DatabaseUnavailableError(
            message="Database is unavailable."
        )

        with self.assertRaises(ApiError) as ctx:
            self.service.create_account(
                email="test@umanitoba.ca",
                password="Password1",
                fname="John",
                lname="Smith",
            )

        self.assertEqual(ctx.exception.status_code, 503)



    # def test_create_account_unknown_exception_maps_to_500(self) -> None:
    #     self.manager.create_account.side_effect = RuntimeError("RTE")

    #     with self.assertRaises(AppError) as ctx:
    #         self.service.create_account(
    #             email="test@umanitoba.ca",
    #             password="Password1",
    #             fname="John",
    #             lname="Smith",
    #         )

    #     self.assertEqual(ctx.exception.status_code, 500)
    #     self.assertEqual(ctx.exception.message, "Internal server error")
    def test_create_account_unknown_exception_maps_to_500(self) -> None:
        self.manager.create_account.side_effect = RuntimeError("RTE")

        with self.assertRaises(ApiError) as ctx:
            self.service.create_account(
                email="test@umanitoba.ca",
                password="Password1",
                fname="John",
                lname="Smith",
            )

        self.assertEqual(ctx.exception.status_code, 500)
 

    
    # -----------------------------
    # get_account_by_userid
    # -----------------------------
    # def test_get_account_by_userid_none_raises_api_400(self) -> None:
    #     with self.assertRaises(ApiError) as ctx:
    #         self.service.get_account_by_userid(None)  # type: ignore[arg-type]

    #     self.assertEqual(ctx.exception.status_code, 400)


    # def test_login_missing_fields_raises_api_400(self) -> None:
    #     with self.assertRaises(ApiError) as ctx:
    #         self.service.login("", "")

    #     self.assertEqual(ctx.exception.status_code, 400)

    # def test_login_valid_mock_user_returns_jwt(self) -> None:
    #     token = self.service.login("test1@gmail.com", "test")
    #     self.assertTrue(isinstance(token, str) and len(token) > 10)

    #     payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    #     self.assertEqual(payload.get("sub"), "test1@gmail.com")
    #     self.assertIn("exp", payload)

    # def test_login_invalid_credentials_raises_api_401(self) -> None:
    #     with self.assertRaises(ApiError) as ctx:
    #         self.service.login("nope@umanitoba.ca", "Password1")

    #     self.assertEqual(ctx.exception.status_code, 401)
