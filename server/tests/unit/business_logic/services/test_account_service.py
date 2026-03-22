from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
import datetime
import jwt

from src.business_logic.services.account_service import AccountService
from src.domain_models import Account

from src.api.errors import ApiError
from src.utils.errors import (
    ValidationError,
    DatabaseUnavailableError,
    AccountAlreadyExistsError,
)
from src.utils import (
    TokenNotFoundError,
    TokenExpiredError,
    TokenAlreadyUsedError,
    EmailVerificationError,
)

SECRET_KEY="change-me"

class TestAccountServiceUnit(unittest.TestCase):
    def setUp(self) -> None:
        self.account_manager: MagicMock = MagicMock(name="account_manager")
        self.token_db: MagicMock = MagicMock(name="token_db")
        self.service = AccountService(
            account_manager=self.account_manager,
            token_db=self.token_db,
        )


    # -----------------------------
    # validate_email / validate_password / validate_account
    # -----------------------------
    def test_validate_email_rejects_non_allowed_domain(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.validate_email("test@gmail.com")

    def test_validate_email_accepts_umanitoba_domain(self) -> None:
        # should not raise
        self.service.validate_email("x@umanitoba.ca")

    def test_validate_password_rejects_weak_password(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.validate_password("password")

    def test_validate_password_accepts_strong_password(self) -> None:
        # should not raise
        self.service.validate_password("StrongPass1")

    def test_validate_account_returns_normalized_fields(self) -> None:
        email, pw, fn, ln = self.service.validate_account(
            "  TEST@UMANITOBA.CA  ",
            "StrongPass1",
            "  John  ",
            "  Doe  ",
        )
        self.assertEqual(email, "test@umanitoba.ca")
        self.assertEqual(pw, "StrongPass1")
        self.assertEqual(fn, "John")
        self.assertEqual(ln, "Doe")

    # -----------------------------
    # create_account
    # -----------------------------
    def test_create_account_success_delegates_to_manager(self) -> None:
        created = Account(
            account_id=123,
            email="test@umanitoba.ca",
            password="StrongPass1",
            fname="John",
            lname="Smith",
            verified=False,
        )
        self.account_manager.create_account.return_value = created

        out = self.service.create_account(
            email="test@umanitoba.ca",
            password="StrongPass1",
            fname="John",
            lname="Smith",
        )

        self.assertIs(out, created)
        self.account_manager.create_account.assert_called_once()
        passed_account: Account = self.account_manager.create_account.call_args[0][0]
        self.assertEqual(passed_account.email, "test@umanitoba.ca")

    def test_create_account_returns_input_account_when_manager_returns_none(
        self,
    ) -> None:
        self.account_manager.create_account.return_value = None

        out = self.service.create_account(
            email="test@umanitoba.ca",
            password="StrongPass1",
            fname="John",
            lname="Smith",
        )

        self.assertIsInstance(out, Account)
        self.assertEqual(out.email, "test@umanitoba.ca")

    def test_create_account_rejects_non_umanitoba_domain(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.create_account(
                email="test@gmail.com",
                password="StrongPass1",
                fname="John",
                lname="Smith",
            )
        self.account_manager.create_account.assert_not_called()

    def test_create_account_rejects_weak_password(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.create_account(
                email="test@umanitoba.ca",
                password="password",
                fname="John",
                lname="Smith",
            )
        self.account_manager.create_account.assert_not_called()

    def test_create_account_duplicate_email_raises_accountalreadyexists(self) -> None:
        self.account_manager.create_account.side_effect = AccountAlreadyExistsError(
            message="Account already exists",
            details={"email": "dup@umanitoba.ca"},
        )

        with self.assertRaises(AccountAlreadyExistsError) as ctx:
            self.service.create_account(
                email="dup@umanitoba.ca",
                password="StrongPass1",
                fname="A",
                lname="B",
            )

        self.assertEqual(getattr(ctx.exception, "status_code", None), 409)

    def test_create_account_manager_validation_error_maps_to_422(self) -> None:
        self.account_manager.create_account.side_effect = ValidationError("bad data")

        with self.assertRaises(ApiError) as ctx:
            self.service.create_account(
                email="test@umanitoba.ca",
                password="StrongPass1",
                fname="John",
                lname="Doe",
            )

        self.assertEqual(ctx.exception.status_code, 422)

    def test_create_account_db_unavailable_maps_to_503(self) -> None:
        self.account_manager.create_account.side_effect = DatabaseUnavailableError(
            message="Database is unavailable."
        )

        with self.assertRaises(ApiError) as ctx:
            self.service.create_account(
                email="test@umanitoba.ca",
                password="StrongPass1",
                fname="John",
                lname="Smith",
            )

        self.assertEqual(ctx.exception.status_code, 503)

    def test_create_account_unknown_exception_maps_to_500(self) -> None:
        self.account_manager.create_account.side_effect = RuntimeError("RTE")

        with self.assertRaises(ApiError) as ctx:
            self.service.create_account(
                email="test@umanitoba.ca",
                password="StrongPass1",
                fname="John",
                lname="Smith",
            )

        self.assertEqual(ctx.exception.status_code, 500)

        msg = getattr(ctx.exception, "message", None)
        if isinstance(msg, str):
            self.assertEqual(msg, "Internal server error")
        else:
            self.assertIn("Internal server error", str(ctx.exception))

    # -----------------------------
    # generate_and_store_verification_token
    # -----------------------------
    def test_generate_and_store_verification_token_stores_token_and_returns_raw(
        self,
    ) -> None:
        raw = "rawtoken123"
        token_hash = "hash123"
        expires_at = MagicMock(name="expires_at")

        with patch(
            "src.business_logic.services.account_service.TokenGenerator.create_token_pair",
            return_value=(raw, token_hash, expires_at),
        ):
            out = self.service.generate_and_store_verification_token(account_id=77)

        self.assertEqual(out, raw)
        self.token_db.add.assert_called_once()
        passed_token = self.token_db.add.call_args[0][0]
        self.assertEqual(passed_token.account_id, 77)
        self.assertEqual(passed_token.token_hash, token_hash)
        self.assertEqual(passed_token.expires_at, expires_at)

    # -----------------------------
    # verify_email_token
    # -----------------------------
    def test_verify_email_token_empty_raises_email_verification_error(self) -> None:
        with self.assertRaises(EmailVerificationError):
            self.service.verify_email_token("")

    def test_verify_email_token_not_found_raises_token_not_found(self) -> None:
        with patch(
            "src.business_logic.services.account_service.TokenGenerator.hash_token",
            return_value="hashed",
        ):
            self.token_db.get_by_hash.return_value = None

            with self.assertRaises(TokenNotFoundError):
                self.service.verify_email_token("rawtoken")

            self.token_db.get_by_hash.assert_called_once_with("hashed")

    def test_verify_email_token_already_used_raises_token_already_used(self) -> None:
        db_token = MagicMock()
        db_token.used = True
        db_token.id = 10
        db_token.account_id = 1

        with patch(
            "src.business_logic.services.account_service.TokenGenerator.hash_token",
            return_value="hashed",
        ):
            self.token_db.get_by_hash.return_value = db_token

            with self.assertRaises(TokenAlreadyUsedError):
                self.service.verify_email_token("rawtoken")

    def test_verify_email_token_expired_raises_token_expired(self) -> None:
        db_token = MagicMock()
        db_token.used = False
        db_token.id = 10
        db_token.account_id = 1
        db_token.expires_at = MagicMock()
        db_token.is_expired.return_value = True

        with patch(
            "src.business_logic.services.account_service.TokenGenerator.hash_token",
            return_value="hashed",
        ):
            self.token_db.get_by_hash.return_value = db_token

            with self.assertRaises(TokenExpiredError):
                self.service.verify_email_token("rawtoken")

    def test_verify_email_token_happy_path_marks_used_and_returns_verified_account(
        self,
    ) -> None:
        db_token = MagicMock()
        db_token.used = False
        db_token.id = 10
        db_token.account_id = 123
        db_token.is_expired.return_value = False

        with patch(
            "src.business_logic.services.account_service.TokenGenerator.hash_token",
            return_value="hashed",
        ):
            self.token_db.get_by_hash.return_value = db_token

            account = self.service.verify_email_token("rawtoken")

        self.assertIsInstance(account, Account)
        self.assertTrue(account.verified)
        self.token_db.mark_used.assert_called_once_with(10)

    # -----------------------------
    # get_account_by_userid (hardcoded in your code)
    # -----------------------------
    def test_get_account_by_userid_none_raises_400(self) -> None:
        with self.assertRaises(ApiError) as ctx:
            self.service.get_account_by_userid(None)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_get_account_by_userid_returns_dummy_account(self) -> None:
        out = self.service.get_account_by_userid("anything")
        self.assertIsInstance(out, Account)
        self.assertEqual(out.id, 1)

    # -----------------------------
    # get_account_userid (manager-based)
    # -----------------------------
    def test_get_account_userid_none_raises_400(self) -> None:
        with self.assertRaises(ApiError) as ctx:
            self.service.get_account_userid(None)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_get_account_userid_not_found_raises_404(self) -> None:
        self.account_manager.get_account_by_id.return_value = None
        with self.assertRaises(ApiError) as ctx:
            self.service.get_account_userid(99)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_get_account_userid_success_returns_account(self) -> None:
        acc = MagicMock(spec=Account)
        self.account_manager.get_account_by_id.return_value = acc
        out = self.service.get_account_userid(5)
        self.assertIs(out, acc)
        self.account_manager.get_account_by_id.assert_called_once_with(5)

    # -----------------------------
    # get_account_by_email
    # -----------------------------
    def test_get_account_by_email_empty_raises_400(self) -> None:
        with self.assertRaises(ApiError) as ctx:
            self.service.get_account_by_email("")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_get_account_by_email_not_found_raises_404(self) -> None:
        self.account_manager.get_account_by_email.return_value = None
        with self.assertRaises(ApiError) as ctx:
            self.service.get_account_by_email("a@umanitoba.ca")
        self.assertEqual(ctx.exception.status_code, 404)

    def test_get_account_by_email_success_returns_account(self) -> None:
        acc = MagicMock(spec=Account)
        self.account_manager.get_account_by_email.return_value = acc
        out = self.service.get_account_by_email("a@umanitoba.ca")
        self.assertIs(out, acc)

    # -----------------------------
    # login
    # -----------------------------
    def test_login_missing_fields_raises_400(self) -> None:
        with self.assertRaises(ApiError) as ctx:
            self.service.login("", "")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_login_nonexistent_email_raises_401(self) -> None:
        self.account_manager.get_account_by_email.return_value = None
        with self.assertRaises(ApiError) as ctx:
            self.service.login("nope@umanitoba.ca", "StrongPass1")
        self.assertEqual(ctx.exception.status_code, 401)

    def test_login_wrong_password_raises_401(self) -> None:
        account = Account(
            account_id=1,
            email="test@umanitoba.ca",
            password="StrongPass1",
            fname="John",
            lname="Smith",
            verified=False,
        )
        self.account_manager.get_account_by_email.return_value = account

        with self.assertRaises(ApiError) as ctx:
            self.service.login("test@umanitoba.ca", "WrongPass1")
        self.assertEqual(ctx.exception.status_code, 401)

    def test_login_success_returns_token(self) -> None:
        account = Account(
            account_id=1,
            email="test@umanitoba.ca",
            password="StrongPass1",
            fname="John",
            lname="Smith",
            verified=False,
        )
        self.account_manager.get_account_by_email.return_value = account

        with patch(
            "src.business_logic.services.account_service.jwt.encode",
            return_value="tok123",
        ) as enc:
            token = self.service.login("test@umanitoba.ca", "StrongPass1")

        self.assertEqual(token, "tok123")
        self.assertTrue(enc.called)


    def test_validate_email_uses_last_domain_segment(self):
        # Correct code uses split("@")[-1], so this should accept "umanitoba.ca".
        # Mutants using [1] or [+1] would incorrectly read "dept" and raise.
        self.service.validate_email("student@dept@umanitoba.ca")


    def test_get_account_by_userid_returns_unverified_account(self):
        account = self.service.get_account_by_userid("123")

        self.assertFalse(account.verified)
        self.assertEqual(account.id, 1)
        self.assertEqual(account.email, "test1@gmail.com")


    def test_login_raises_when_email_missing(self):
        with self.assertRaises(ApiError) as ctx:
            self.service.login("", "ValidPass1")

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception._message, "Email and password are required")


    def test_login_raises_when_password_missing(self):
        with self.assertRaises(ApiError) as ctx:
            self.service.login("user@umanitoba.ca", "")

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception._message, "Email and password are required")


    @patch("src.business_logic.services.account_service.jwt.encode")
    def test_login_raises_for_wrong_password_when_stored_password_is_lexicographically_greater(
        self, mock_encode
    ):
        account = Account(
            email="user@umanitoba.ca",
            password="zPassword9",
            fname="Test",
            lname="User",
            account_id=7,
            verified=True,
        )
        self.account_manager.get_account_by_email.return_value = account

        with self.assertRaises(ApiError) as ctx:
            self.service.login("user@umanitoba.ca", "aPassword9")

        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception._message, "Invalid email or password")
        mock_encode.assert_not_called()


    @patch("src.business_logic.services.account_service.jwt.encode")
    def test_login_allows_equal_passwords_even_when_distinct_string_objects(
        self, mock_encode
    ):
        stored_password = "ValidPass1"
        supplied_password = "".join(["Valid", "Pass", "1"])

        self.assertEqual(stored_password, supplied_password)
        self.assertIsNot(stored_password, supplied_password)

        account = Account(
            email="user@umanitoba.ca",
            password=stored_password,
            fname="Test",
            lname="User",
            account_id=7,
            verified=True,
        )
        self.account_manager.get_account_by_email.return_value = account
        mock_encode.return_value = "fake-jwt"

        token = self.service.login("user@umanitoba.ca", supplied_password)

        self.assertEqual(token, "fake-jwt")
        mock_encode.assert_called_once()


    @patch("src.business_logic.services.account_service.jwt.encode")
    @patch("src.business_logic.services.account_service.datetime.datetime")
    def test_login_sets_expiration_to_exactly_30_days(self, mock_datetime, mock_encode):
        frozen_now = datetime.datetime(2026, 3, 21, 12, 0, 0, tzinfo=datetime.timezone.utc)
        mock_datetime.now.return_value = frozen_now

        account = Account(
            email="user@umanitoba.ca",
            password="ValidPass1",
            fname="Test",
            lname="User",
            account_id=7,
            verified=True,
        )
        self.account_manager.get_account_by_email.return_value = account
        mock_encode.return_value = "fake-jwt"

        token = self.service.login("user@umanitoba.ca", "ValidPass1")

        self.assertEqual(token, "fake-jwt")

        payload = mock_encode.call_args.args[0]
        self.assertEqual(
            payload["exp"],
            frozen_now + datetime.timedelta(days=30),
        )

    def test_login_token_expiration_is_exactly_30_days(self):
        frozen_now = datetime.datetime(2026, 3, 21, 12, 0, 0, tzinfo=datetime.timezone.utc)

        account = Account(
            email="user@umanitoba.ca",
            password="ValidPass1",
            fname="Test",
            lname="User",
            account_id=7,
            verified=True,
        )
        # account.id = 7

        self.account_manager.get_account_by_email.return_value = account

        with patch(
            "src.business_logic.services.account_service.datetime.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = frozen_now

            token = self.service.login("user@umanitoba.ca", "ValidPass1")

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_exp": False},
        )

        expected_exp = frozen_now + datetime.timedelta(days=30)
        expected_exp_timestamp = int(expected_exp.timestamp())

        self.assertEqual(payload["sub"], "7")
        self.assertEqual(payload["exp"], expected_exp_timestamp)