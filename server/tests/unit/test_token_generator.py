import unittest
from datetime import datetime, timedelta

from src.utils import TokenGenerator


class TestTokenGenerator(unittest.TestCase):
    """Unit tests for TokenGenerator utility class."""

    # -------------------------
    # generate_token Tests
    # -------------------------
    def test_generate_token_ShouldReturn64CharHexString(self) -> None:
        token = TokenGenerator.generate_token()
        self.assertEqual(len(token), 64)
        # Should be valid hex
        try:
            int(token, 16)
        except ValueError:
            self.fail("Token is not valid hex")

    def test_generate_token_ShouldProduceDifferentTokensEachCall(self) -> None:
        token1 = TokenGenerator.generate_token()
        token2 = TokenGenerator.generate_token()
        self.assertNotEqual(token1, token2)

    # -------------------------
    # hash_token Tests
    # -------------------------
    def test_hash_token_ShouldReturn64CharHexString(self) -> None:
        token = TokenGenerator.generate_token()
        hashed = TokenGenerator.hash_token(token)
        self.assertEqual(len(hashed), 64)

    def test_hash_token_ShouldBeConsistent(self) -> None:
        token = "test-token-123"
        hash1 = TokenGenerator.hash_token(token)
        hash2 = TokenGenerator.hash_token(token)
        self.assertEqual(hash1, hash2)

    def test_hash_token_DifferentTokens_ShouldProduceDifferentHashes(self) -> None:
        hash1 = TokenGenerator.hash_token("token1")
        hash2 = TokenGenerator.hash_token("token2")
        self.assertNotEqual(hash1, hash2)

    def test_hash_token_EmptyToken_ShouldRaiseValueError(self) -> None:
        with self.assertRaises(ValueError):
            TokenGenerator.hash_token("")

    # -------------------------
    # get_expiry_time Tests
    # -------------------------
    def test_get_expiry_time_ShouldReturnFutureTime(self) -> None:
        now = datetime.now()
        expiry = TokenGenerator.get_expiry_time()
        self.assertGreater(expiry, now)

    def test_get_expiry_time_ShouldBeApproximately5MinutesInFuture(self) -> None:
        now = datetime.now()
        expiry = TokenGenerator.get_expiry_time()
        delta = expiry - now
        # Should be 5 minutes (allow 1 second margin)
        expected_delta = timedelta(minutes=5)
        self.assertLessEqual(abs(delta.total_seconds() - expected_delta.total_seconds()), 1)

    # -------------------------
    # create_token_pair Tests
    # -------------------------
    def test_create_token_pair_ShouldReturnTuple(self) -> None:
        result = TokenGenerator.create_token_pair()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

    def test_create_token_pair_RawTokenAndHashDiffer(self) -> None:
        raw_token, token_hash, expires_at = TokenGenerator.create_token_pair()
        self.assertNotEqual(raw_token, token_hash)

    def test_create_token_pair_HashEqualsHashOfRawToken(self) -> None:
        raw_token, token_hash, expires_at = TokenGenerator.create_token_pair()
        computed_hash = TokenGenerator.hash_token(raw_token)
        self.assertEqual(token_hash, computed_hash)

    def test_create_token_pair_ExpiryIsInFuture(self) -> None:
        raw_token, token_hash, expires_at = TokenGenerator.create_token_pair()
        self.assertGreater(expires_at, datetime.now())

    def test_create_token_pair_ExpiryIsApproximately5Minutes(self) -> None:
        now = datetime.now()
        raw_token, token_hash, expires_at = TokenGenerator.create_token_pair()
        delta = expires_at - now
        expected_delta = timedelta(minutes=5)
        self.assertLessEqual(abs(delta.total_seconds() - expected_delta.total_seconds()), 1)


if __name__ == "__main__":
    unittest.main()
