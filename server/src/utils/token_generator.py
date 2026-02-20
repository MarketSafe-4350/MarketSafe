import secrets
import hashlib
from datetime import datetime, timedelta


class TokenGenerator:
    """
    Utility class for generating and hashing verification tokens.

    Design:
    - Uses cryptographically secure random token generation
    - Tokens are hashed before storage (one-way hashing)
    - Raw token is only sent to user via email
    - Database stores only the hash
    """

    # Token configuration
    TOKEN_LENGTH = 32  # bytes, produces 64 character hex string
    TOKEN_EXPIRY_MINUTES = 5  # tokens expire after 5 minutes

    @staticmethod
    def generate_token() -> str:
        """
        Generate a cryptographically secure random token.

        Returns:
            str: A hex-encoded random token (64 characters)
        """
        raw_bytes = secrets.token_bytes(TokenGenerator.TOKEN_LENGTH)
        return raw_bytes.hex()

    @staticmethod
    def hash_token(token: str) -> str:
        """
        Hash a token using SHA-256.

        Args:
            token (str): The raw token to hash

        Returns:
            str: The hex-encoded SHA-256 hash of the token
        """
        if not token:
            raise ValueError("Token cannot be empty")
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def get_expiry_time() -> datetime:
        """
        Get the expiry timestamp for a new token.

        Returns:
            datetime: The expiry time (current time + TOKEN_EXPIRY_MINUTES)
        """
        return datetime.now() + timedelta(minutes=TokenGenerator.TOKEN_EXPIRY_MINUTES)

    @staticmethod
    def create_token_pair() -> tuple[str, str, datetime]:
        """
        Create a new token pair with expiry time.

        This is a convenience method that generates a token, hashes it,
        and returns both the raw token and hash along with expiry time.

        Returns:
            tuple: (raw_token, token_hash, expires_at)
                - raw_token: The token to send to the user (via email link)
                - token_hash: The hashed token to store in the database
                - expires_at: The expiry timestamp
        """
        raw_token = TokenGenerator.generate_token()
        token_hash = TokenGenerator.hash_token(raw_token)
        expires_at = TokenGenerator.get_expiry_time()
        return raw_token, token_hash, expires_at
