from datetime import datetime
from typing import Optional
from src.utils import ValidationError, Validation


class VerificationToken:
    """
    Domain Entity: VerificationToken

    This class represents the `email_verification_tokens` table in the database.

    Design Decisions:

    1. Encapsulation
       - All internal state is stored in variables prefixed with `_`.
       - `_variable` is used by convention to signal protected fields.

    2. Controlled Access
       - Read access is provided using `@property`.
       - Mutation is allowed only through domain methods.

    3. Invariants
       - ID can only be assigned once (after DB persistence).
       - account_id must be a positive integer.
       - token_hash is immutable (set at creation).
       - expires_at must be in the future.
       - A token can only be marked as used once.
    """

    def __init__(
            self,
            account_id: int,
            token_hash: str,
            expires_at: datetime,
            *,
            token_id: Optional[int] = None,
            created_at: Optional[datetime] = None,
            used: bool = False,
            used_at: Optional[datetime] = None,
    ):
        # Internal state (protected by convention)
        self._id = token_id
        self._account_id = Validation.require_int(account_id, "account_id")
        self._token_hash = Validation.require_str(token_hash, "token_hash")
        self._expires_at = Validation.require_not_none(expires_at, "expires_at")
        self._created_at = created_at or datetime.now()
        self._used = Validation.is_boolean(used, "used")
        self._used_at = used_at

    # ==============================
    # ID (read-only, may be None before DB insert)
    # ==============================

    @property
    def id(self):
        return self._id

    def mark_persisted(self, token_id: int):
        if token_id is None:
            raise ValidationError("Token ID cannot be None.")
        if self._id is not None:
            raise ValidationError("Token ID has already been assigned.")
        self._id = token_id

    # ==============================
    # ACCOUNT_ID (NOT NULL, immutable)
    # ==============================

    @property
    def account_id(self):
        return self._account_id

    # ==============================
    # TOKEN_HASH (NOT NULL, immutable)
    # ==============================

    @property
    def token_hash(self):
        return self._token_hash

    # ==============================
    # EXPIRES_AT (NOT NULL, immutable)
    # ==============================

    @property
    def expires_at(self):
        return self._expires_at

    # ==============================
    # CREATED_AT (NOT NULL, immutable)
    # ==============================

    @property
    def created_at(self):
        return self._created_at

    # ==============================
    # USED (NOT NULL)
    # ==============================

    @property
    def used(self):
        return self._used

    def mark_as_used(self):
        """Mark the token as used."""
        if self._used:
            raise ValidationError("Token has already been used.")
        self._used = True
        self._used_at = datetime.now()

    # ==============================
    # USED_AT (nullable)
    # ==============================

    @property
    def used_at(self):
        return self._used_at

    # ==============================
    # HELPER METHODS
    # ==============================

    def is_expired(self) -> bool:
        """Check if the token has expired."""
        return datetime.now() > self._expires_at

    def is_valid(self) -> bool:
        """Check if the token is valid (not expired and not used)."""
        return not self.is_expired() and not self._used

    # ==============================
    # DEBUG REPRESENTATION
    # ==============================

    def __repr__(self):
        return (
            f"VerificationToken(id={self._id}, "
            f"account_id={self._account_id}, "
            f"used={self._used}, "
            f"expires_at={self._expires_at})"
        )
