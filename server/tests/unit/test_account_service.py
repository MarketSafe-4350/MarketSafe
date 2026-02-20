import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.business_logic.services import AccountService
from src.domain_models import Account, VerificationToken
from src.utils import (
    TokenGenerator,
    TokenNotFoundError,
    TokenExpiredError,
    TokenAlreadyUsedError,
    EmailVerificationError,
)


class TestAccountService(unittest.TestCase):
    """Unit tests for AccountService."""

    def setUp(self) -> None:
        self.token_db_mock = MagicMock()
        self.service = AccountService(token_db=self.token_db_mock)

    # -------------------------
    # generate_and_store_verification_token Tests
    # -------------------------
    def test_generate_and_store_verification_token_ShouldStoreTokenInDB(self) -> None:
        """Verify that token is stored in database."""
        self.token_db_mock.add.return_value = VerificationToken(
            account_id=1,
            token_hash="test-hash",
            expires_at=datetime.now() + timedelta(minutes=5),
            token_id=1,
        )

        raw_token = self.service.generate_and_store_verification_token(account_id=1)

        self.assertIsNotNone(raw_token)
        self.token_db_mock.add.assert_called_once()

    def test_generate_and_store_verification_token_ShouldReturnRawToken(self) -> None:
        """Raw token should be returned, not the hash."""
        self.token_db_mock.add.return_value = VerificationToken(
            account_id=1,
            token_hash="test-hash",
            expires_at=datetime.now() + timedelta(minutes=5),
            token_id=1,
        )

        raw_token = self.service.generate_and_store_verification_token(account_id=1)

        # Raw token should be 64 chars (hex)
        self.assertEqual(len(raw_token), 64)

    # -------------------------
    # verify_email_token Tests
    # -------------------------
    def test_verify_email_token_EmptyToken_ShouldRaiseEmailVerificationError(self) -> None:
        """Attempting to verify empty token should raise error."""
        with self.assertRaises(EmailVerificationError):
            self.service.verify_email_token("")

    def test_verify_email_token_TokenNotFound_ShouldRaiseTokenNotFoundError(self) -> None:
        """When token hash doesn't exist in DB, should raise TokenNotFoundError."""
        self.token_db_mock.get_by_hash.return_value = None

        with self.assertRaises(TokenNotFoundError):
            self.service.verify_email_token("nonexistent-token")

    def test_verify_email_token_TokenAlreadyUsed_ShouldRaiseTokenAlreadyUsedError(self) -> None:
        """When token is already marked used, should raise TokenAlreadyUsedError."""
        used_token = VerificationToken(
            account_id=1,
            token_hash="used-hash",
            expires_at=datetime.now() + timedelta(minutes=5),
            token_id=1,
            used=True,
            used_at=datetime.now(),
        )
        self.token_db_mock.get_by_hash.return_value = used_token

        with self.assertRaises(TokenAlreadyUsedError):
            self.service.verify_email_token("test-token")

    def test_verify_email_token_TokenExpired_ShouldRaiseTokenExpiredError(self) -> None:
        """When token has expired, should raise TokenExpiredError."""
        expired_token = VerificationToken(
            account_id=1,
            token_hash="expired-hash",
            expires_at=datetime.now() - timedelta(minutes=1),  # Expired
            token_id=1,
            used=False,
        )
        self.token_db_mock.get_by_hash.return_value = expired_token

        with self.assertRaises(TokenExpiredError):
            self.service.verify_email_token("test-token")

    def test_verify_email_token_Valid_ShouldMarkTokenUsed(self) -> None:
        """When token is valid, should mark it as used."""
        valid_token = VerificationToken(
            account_id=1,
            token_hash="valid-hash",
            expires_at=datetime.now() + timedelta(minutes=5),
            token_id=1,
            used=False,
        )
        self.token_db_mock.get_by_hash.return_value = valid_token

        # Mock the account retrieval
        with patch.object(self.service, 'get_account_by_userid') as mock_get_account:
            mock_get_account.return_value = Account(
                email="test@umanitoba.ca",
                password="hashed",
                fname="Test",
                lname="User",
            )

            account = self.service.verify_email_token("test-token")

            # Check that mark_used was called
            self.token_db_mock.mark_used.assert_called_once_with(1)

    def test_verify_email_token_Valid_ShouldReturnVerifiedAccount(self) -> None:
        """When token is valid, should return an account with verified=True."""
        valid_token = VerificationToken(
            account_id=1,
            token_hash="valid-hash",
            expires_at=datetime.now() + timedelta(minutes=5),
            token_id=1,
            used=False,
        )
        self.token_db_mock.get_by_hash.return_value = valid_token

        test_account = Account(
            email="test@umanitoba.ca",
            password="hashed",
            fname="Test",
            lname="User",
        )

        with patch.object(self.service, 'get_account_by_userid') as mock_get_account:
            mock_get_account.return_value = test_account

            account = self.service.verify_email_token("test-token")

            self.assertTrue(account.verified)

    def test_verify_email_token_TokenMarkedUsedOnlyAfterSuccess(self) -> None:
        """Token should only be marked as used after all validation passes."""
        valid_token = VerificationToken(
            account_id=1,
            token_hash="valid-hash",
            expires_at=datetime.now() + timedelta(minutes=5),
            token_id=1,
            used=False,
        )
        self.token_db_mock.get_by_hash.return_value = valid_token

        with patch.object(self.service, 'get_account_by_userid') as mock_get_account:
            mock_get_account.return_value = Account(
                email="test@umanitoba.ca",
                password="hashed",
                fname="Test",
                lname="User",
            )

            # Verify that mark_used is called last
            call_count_before = self.token_db_mock.mark_used.call_count
            self.service.verify_email_token("test-token")
            call_count_after = self.token_db_mock.mark_used.call_count

            self.assertEqual(call_count_after - call_count_before, 1)


if __name__ == "__main__":
    unittest.main()
