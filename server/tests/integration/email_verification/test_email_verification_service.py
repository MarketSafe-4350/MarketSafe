from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from src.business_logic.services import AccountService
from src.db import DBUtility
from src.db.email_verification_token.mysql import MySQLEmailVerificationTokenDB
from src.domain_models import VerificationToken
from src.utils import (
    TokenGenerator,
    TokenNotFoundError,
    TokenExpiredError,
    TokenAlreadyUsedError,
)
from tests.helpers import integration_db


class TestEmailVerificationServiceIntegration(unittest.TestCase):
    """Integration tests for email verification workflow."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up database connection."""
        cls.db = integration_db.get_db_instance()
        integration_db.setup_tokens_table(cls.db)

    def setUp(self) -> None:
        """Clear tokens and initialize service."""
        integration_db.clear_tokens_table(self.db)
        self.token_db = MySQLEmailVerificationTokenDB(db=self.db)
        self.service = AccountService(token_db=self.token_db)

    # -------------------------
    # Full Verification Workflow Tests
    # -------------------------
    def test_complete_verification_flow_Success(self) -> None:
        """Test full flow: generate token -> store -> verify."""
        # Step 1: Generate token
        raw_token = self.service.generate_and_store_verification_token(account_id=1)
        self.assertEqual(len(raw_token), 64)

        # Step 2: Verify it's in DB
        token_hash = TokenGenerator.hash_token(raw_token)
        db_token = self.token_db.get_by_hash(token_hash)
        self.assertIsNotNone(db_token)
        self.assertFalse(db_token.used)

        # Step 3: Verify the token successfully
        account = self.service.verify_email_token(raw_token)
        self.assertTrue(account.verified)

        # Step 4: Verify token is now marked as used
        final_token = self.token_db.get_by_hash(token_hash)
        self.assertTrue(final_token.used)
        self.assertIsNotNone(final_token.used_at)

    def test_expired_token_cannot_be_verified(self) -> None:
        """Test that expired tokens cannot be verified."""
        # Create expired token directly in DB
        expired_token = VerificationToken(
            account_id=1,
            token_hash="expired-hash",
            expires_at=datetime.now() - timedelta(minutes=1),  # Already expired
        )
        self.token_db.add(expired_token)

        # Mock the raw token for hashing check
        raw_token = "test-token-that-hashes-to-expired-hash"

        # Try to verify and expect TokenExpiredError
        with self.assertRaises(TokenExpiredError):
            self.service.verify_email_token(raw_token)

    def test_token_cannot_be_used_twice(self) -> None:
        """Test that a token cannot be verified twice."""
        # Generate and store token
        raw_token = self.service.generate_and_store_verification_token(account_id=1)

        # First verification should succeed
        account = self.service.verify_email_token(raw_token)
        self.assertTrue(account.verified)

        # Second verification should fail
        with self.assertRaises(TokenAlreadyUsedError):
            self.service.verify_email_token(raw_token)

    def test_multiple_accounts_separate_tokens(self) -> None:
        """Test that different accounts can have their own tokens."""
        # Generate tokens for two different accounts
        raw_token_1 = self.service.generate_and_store_verification_token(account_id=1)
        raw_token_2 = self.service.generate_and_store_verification_token(account_id=2)

        # Tokens should be different
        self.assertNotEqual(raw_token_1, raw_token_2)

        # Both should be retrievable
        hash1 = TokenGenerator.hash_token(raw_token_1)
        hash2 = TokenGenerator.hash_token(raw_token_2)

        db_token_1 = self.token_db.get_by_hash(hash1)
        db_token_2 = self.token_db.get_by_hash(hash2)

        self.assertIsNotNone(db_token_1)
        self.assertIsNotNone(db_token_2)
        self.assertEqual(db_token_1.account_id, 1)
        self.assertEqual(db_token_2.account_id, 2)

    def test_token_retrieval_by_account(self) -> None:
        """Test getting the latest token for an account."""
        # Generate multiple tokens for same account
        self.service.generate_and_store_verification_token(account_id=1)
        raw_token_latest = self.service.generate_and_store_verification_token(account_id=1)

        # Get latest
        latest = self.token_db.get_latest_by_account(account_id=1)
        self.assertIsNotNone(latest)

        # Verify it's the most recent
        latest_hash = TokenGenerator.hash_token(raw_token_latest)
        self.assertEqual(latest.token_hash, latest_hash)

    def test_token_expiry_is_5_minutes(self) -> None:
        """Verify that generated tokens expire in 5 minutes."""
        from datetime import datetime
        
        now = datetime.now()
        raw_token = self.service.generate_and_store_verification_token(account_id=1)
        
        token_hash = TokenGenerator.hash_token(raw_token)
        db_token = self.token_db.get_by_hash(token_hash)
        
        expiry_delta = db_token.expires_at - now
        # Should be approximately 5 minutes (300 seconds)
        # Allow up to 2 seconds margin
        self.assertLess(abs(expiry_delta.total_seconds() - 300), 2)

    def test_cleanup_used_tokens(self) -> None:
        """Test that used tokens can be cleaned up."""
        # Generate 3 tokens
        raw_token_1 = self.service.generate_and_store_verification_token(account_id=1)
        raw_token_2 = self.service.generate_and_store_verification_token(account_id=1)
        raw_token_3 = self.service.generate_and_store_verification_token(account_id=1)

        # Verify first two
        self.service.verify_email_token(raw_token_1)
        self.service.verify_email_token(raw_token_2)

        # Clear used tokens
        cleared = self.token_db.clear_used_tokens(account_id=1)
        self.assertEqual(cleared, 2)

        # Third token should still exist
        latest = self.token_db.get_latest_by_account(account_id=1)
        self.assertIsNotNone(latest)
        hash_3 = TokenGenerator.hash_token(raw_token_3)
        self.assertEqual(latest.token_hash, hash_3)


if __name__ == "__main__":
    unittest.main()
