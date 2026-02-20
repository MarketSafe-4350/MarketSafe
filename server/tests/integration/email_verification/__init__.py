from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from src.db import DBUtility
from src.db.email_verification_token.mysql import MySQLEmailVerificationTokenDB
from src.domain_models import VerificationToken
from src.utils import TokenGenerator, DatabaseQueryError, TokenNotFoundError
from tests.helpers import integration_db


class TestMySQLEmailVerificationTokenDB(unittest.TestCase):
    """Integration tests for MySQLEmailVerificationTokenDB."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up database connection for all tests."""
        cls.db = integration_db.get_db_instance()
        # Create the table if it doesn't exist
        integration_db.setup_tokens_table(cls.db)

    def setUp(self) -> None:
        """Clear tokens table before each test."""
        integration_db.clear_tokens_table(self.db)
        self.token_db = MySQLEmailVerificationTokenDB(db=self.db)

    # -------------------------
    # add (INSERT) Tests
    # -------------------------
    def test_add_ShouldInsertTokenIntoDatabase(self) -> None:
        """Should successfully insert a new token."""
        token = VerificationToken(
            account_id=1,
            token_hash="test-hash-123",
            expires_at=datetime.now() + timedelta(minutes=5),
        )

        result = self.token_db.add(token)

        self.assertIsNotNone(result.id)
        self.assertEqual(result.account_id, 1)
        self.assertEqual(result.token_hash, "test-hash-123")

    def test_add_ShouldAssignAutoIncrementID(self) -> None:
        """Inserted token should have auto-assigned ID."""
        token1 = VerificationToken(
            account_id=1,
            token_hash="hash-1",
            expires_at=datetime.now() + timedelta(minutes=5),
        )
        token2 = VerificationToken(
            account_id=1,
            token_hash="hash-2",
            expires_at=datetime.now() + timedelta(minutes=5),
        )

        result1 = self.token_db.add(token1)
        result2 = self.token_db.add(token2)

        self.assertIsNotNone(result1.id)
        self.assertIsNotNone(result2.id)
        self.assertLess(result1.id, result2.id)

    # -------------------------
    # get_by_hash (READ) Tests
    # -------------------------
    def test_get_by_hash_ShouldRetrieveTokenByHash(self) -> None:
        """Should retrieve a token using its hash."""
        token = VerificationToken(
            account_id=1,
            token_hash="test-hash-123",
            expires_at=datetime.now() + timedelta(minutes=5),
        )
        inserted = self.token_db.add(token)

        retrieved = self.token_db.get_by_hash("test-hash-123")

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, inserted.id)
        self.assertEqual(retrieved.token_hash, "test-hash-123")

    def test_get_by_hash_NonexistentHash_ShouldReturnNone(self) -> None:
        """Getting nonexistent token should return None."""
        result = self.token_db.get_by_hash("nonexistent-hash")
        self.assertIsNone(result)

    # -------------------------
    # get_latest_by_account (READ) Tests
    # -------------------------
    def test_get_latest_by_account_ShouldReturnMostRecentToken(self) -> None:
        """Should return the most recently created token for an account."""
        # Create two tokens for the same account
        token1 = VerificationToken(
            account_id=1,
            token_hash="hash-1",
            expires_at=datetime.now() + timedelta(minutes=5),
        )
        token2 = VerificationToken(
            account_id=1,
            token_hash="hash-2",
            expires_at=datetime.now() + timedelta(minutes=5),
        )

        self.token_db.add(token1)
        self.token_db.add(token2)

        latest = self.token_db.get_latest_by_account(account_id=1)

        self.assertIsNotNone(latest)
        self.assertEqual(latest.token_hash, "hash-2")

    def test_get_latest_by_account_NoTokens_ShouldReturnNone(self) -> None:
        """Getting tokens for account with no tokens should return None."""
        result = self.token_db.get_latest_by_account(account_id=999)
        self.assertIsNone(result)

    # -------------------------
    # mark_used (UPDATE) Tests
    # -------------------------
    def test_mark_used_ShouldUpdateTokenStatus(self) -> None:
        """Marking token as used should update the database."""
        token = VerificationToken(
            account_id=1,
            token_hash="test-hash",
            expires_at=datetime.now() + timedelta(minutes=5),
        )
        inserted = self.token_db.add(token)

        self.token_db.mark_used(inserted.id)

        retrieved = self.token_db.get_by_hash("test-hash")
        self.assertTrue(retrieved.used)
        self.assertIsNotNone(retrieved.used_at)

    def test_mark_used_NonexistentToken_ShouldRaiseTokenNotFoundError(self) -> None:
        """Marking nonexistent token as used should raise error."""
        with self.assertRaises(TokenNotFoundError):
            self.token_db.mark_used(token_id=999)

    # -------------------------
    # clear_used_tokens (DELETE) Tests
    # -------------------------
    def test_clear_used_tokens_ShouldDeleteUsedTokens(self) -> None:
        """Should delete all used tokens for an account."""
        # Create and mark multiple tokens as used
        token1 = VerificationToken(
            account_id=1,
            token_hash="hash-1",
            expires_at=datetime.now() + timedelta(minutes=5),
        )
        token2 = VerificationToken(
            account_id=1,
            token_hash="hash-2",
            expires_at=datetime.now() + timedelta(minutes=5),
        )

        inserted1 = self.token_db.add(token1)
        inserted2 = self.token_db.add(token2)

        self.token_db.mark_used(inserted1.id)
        self.token_db.mark_used(inserted2.id)

        deleted_count = self.token_db.clear_used_tokens(account_id=1)

        self.assertEqual(deleted_count, 2)
        self.assertIsNone(self.token_db.get_by_hash("hash-1"))
        self.assertIsNone(self.token_db.get_by_hash("hash-2"))

    def test_clear_used_tokens_ShouldNotDeleteUnusedTokens(self) -> None:
        """Should only delete used tokens, not unused ones."""
        token_used = VerificationToken(
            account_id=1,
            token_hash="hash-used",
            expires_at=datetime.now() + timedelta(minutes=5),
        )
        token_unused = VerificationToken(
            account_id=1,
            token_hash="hash-unused",
            expires_at=datetime.now() + timedelta(minutes=5),
        )

        inserted_used = self.token_db.add(token_used)
        inserted_unused = self.token_db.add(token_unused)

        self.token_db.mark_used(inserted_used.id)

        deleted_count = self.token_db.clear_used_tokens(account_id=1)

        self.assertEqual(deleted_count, 1)
        self.assertIsNone(self.token_db.get_by_hash("hash-used"))
        self.assertIsNotNone(self.token_db.get_by_hash("hash-unused"))

    # -------------------------
    # Full Workflow Tests
    # -------------------------
    def test_full_verification_workflow(self) -> None:
        """Test the complete token lifecycle: create -> verify -> mark used."""
        # Generate token pair
        raw_token, token_hash, expires_at = TokenGenerator.create_token_pair()

        # Store token
        token = VerificationToken(
            account_id=1,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        inserted = self.token_db.add(token)

        # Retrieve token
        retrieved = self.token_db.get_by_hash(token_hash)
        self.assertIsNotNone(retrieved)
        self.assertFalse(retrieved.used)

        # Mark as used
        self.token_db.mark_used(retrieved.id)

        # Verify it's marked used
        final = self.token_db.get_by_hash(token_hash)
        self.assertTrue(final.used)


if __name__ == "__main__":
    unittest.main()
