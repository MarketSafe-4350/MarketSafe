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
    # login
    # -----------------------------

    def test_login_valid_credentials_returns_token(self) -> None:
        # Arrange: mock existing account
        account = Account(
            account_id=1,
            email="test@umanitoba.ca",
            password="Password1",
            fname="John",
            lname="Smith",
            verified=False,
        )
        self.manager.get_account_by_email.return_value = account

        # Act: login with correct credentials
        token = self.service.login("test@umanitoba.ca", "Password1")

        # Assert: token returned and manager called
        self.assertIsInstance(token, str)
        self.manager.get_account_by_email.assert_called_once_with("test@umanitoba.ca")

    def test_login_missing_fields_raises_400(self) -> None:
        # Act + Assert: empty fields rejected immediately
        with self.assertRaises(ApiError) as ctx:
            self.service.login("", "")

        self.assertEqual(ctx.exception.status_code, 400)
        self.manager.get_account_by_email.assert_not_called()

    def test_login_nonexistent_email_raises_401(self) -> None:
        # Arrange: manager returns None (no account)
        self.manager.get_account_by_email.return_value = None

        # Act + Assert: invalid email should fail
        with self.assertRaises(ApiError) as ctx:
            self.service.login("nope@umanitoba.ca", "Password1")

        self.assertEqual(ctx.exception.status_code, 401)
        self.manager.get_account_by_email.assert_called_once_with("nope@umanitoba.ca")

    def test_login_wrong_password_raises_401(self) -> None:
        # Arrange: account exists but password mismatch
        account = Account(
            account_id=1,
            email="test@umanitoba.ca",
            password="Password1",
            fname="John",
            lname="Smith",
            verified=False,
        )
        self.manager.get_account_by_email.return_value = account

        # Act + Assert: wrong password rejected
        with self.assertRaises(ApiError) as ctx:
            self.service.login("test@umanitoba.ca", "WrongPassword1")

        self.assertEqual(ctx.exception.status_code, 401)

    # -----------------------------
    # get_account_by_userid
    # -----------------------------

    def test_get_account_userid_success_returns_account(self) -> None:
        # Arrange: mock account returned from manager
        account = Account(
            account_id=5,
            email="user@umanitoba.ca",
            password="Password1",
            fname="Jane",
            lname="Doe",
            verified=False,
        )
        self.manager.get_account_by_id.return_value = account

        # Act: fetch by ID
        result = self.service.get_account_userid(5)

        # Assert: correct account returned and manager called
        self.assertEqual(result, account)
        self.manager.get_account_by_id.assert_called_once_with(5)

    def test_get_account_by_userid_none_raises_400(self):
        with self.assertRaises(ApiError) as ctx:
            self.service.get_account_by_userid(None)  # type: ignore[arg-type]

        self.assertEqual(ctx.exception.status_code, 400)
    def test_get_account_userid_not_found_raises_404(self) -> None:
        # Arrange: manager returns None (not found)
        self.manager.get_account_by_id.return_value = None

        # Act + Assert: unknown ID should raise 404
        with self.assertRaises(ApiError) as ctx:
            self.service.get_account_userid(99)

        self.assertEqual(ctx.exception.status_code, 404)
        self.manager.get_account_by_id.assert_called_once_with(99)

    def test_get_account_by_email_empty_raises_400(self):
        with self.assertRaises(ApiError) as ctx:
            self.service.get_account_by_email("")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_get_account_by_email_not_found_raises_404(self):
        self.manager.get_account_by_email.return_value = None

        with self.assertRaises(ApiError) as ctx:
            self.service.get_account_by_email("a@umanitoba.ca")

        self.assertEqual(ctx.exception.status_code, 404)
        self.manager.get_account_by_email.assert_called_once_with("a@umanitoba.ca")

    def test_get_account_by_email_success_returns_account(self):
        acc = MagicMock(spec=Account)
        self.manager.get_account_by_email.return_value = acc

        result = self.service.get_account_by_email("a@umanitoba.ca")

        self.assertIs(result, acc)
        self.manager.get_account_by_email.assert_called_once_with("a@umanitoba.ca")

    def test_create_account_manager_validation_error_maps_to_422(self):
        # IMPORTANT: valid inputs so validate_account() does not fail first
        valid_email = "test@umanitoba.ca"
        valid_password = "StrongPass1"
        fname = "John"
        lname = "Doe"

        # Make the MANAGER raise ValidationError
        self.manager.create_account.side_effect = ValidationError("bad data")

        with self.assertRaises(ApiError) as ctx:
            self.service.create_account(
                valid_email,
                valid_password,
                fname,
                lname,
            )

        self.assertEqual(ctx.exception.status_code, 422)