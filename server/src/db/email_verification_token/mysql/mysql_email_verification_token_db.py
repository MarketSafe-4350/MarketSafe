from __future__ import annotations
from typing import Optional
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing_extensions import override

from src.db import DBUtility
from src.db.email_verification_token import EmailVerificationTokenDB
from src.domain_models import VerificationToken
from src.utils import (Validation, DatabaseQueryError, TokenNotFoundError)


class MySQLEmailVerificationTokenDB(EmailVerificationTokenDB):
    """
    MySQL implementation of email verification token persistence.

    Design:
    - Uses parameterized queries to prevent SQL injection
    - Converts between domain models and database rows using mapping
    - Handles all database-level errors and converts to domain-level exceptions
    """

    def __init__(self, db: DBUtility) -> None:
        super().__init__(db)

    # -------------------------
    # CREATE
    # -------------------------
    @override
    def add(self, token: VerificationToken) -> VerificationToken:
        Validation.require_not_none(token, "token")

        sql = text("""
                   INSERT INTO email_verification_tokens
                   (account_id, token_hash, created_at, expires_at, used, used_at)
                   VALUES (:account_id, :token_hash, :created_at, :expires_at, :used, :used_at)
                   """)

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {
                    "account_id": token.account_id,
                    "token_hash": token.token_hash,
                    "created_at": token.created_at,
                    "expires_at": token.expires_at,
                    "used": bool(token.used),
                    "used_at": token.used_at,
                })

                new_id = int(result.lastrowid)

                # Return the token with the assigned ID
                return VerificationToken(
                    account_id=token.account_id,
                    token_hash=token.token_hash,
                    expires_at=token.expires_at,
                    token_id=new_id,
                    created_at=token.created_at,
                    used=token.used,
                    used_at=token.used_at,
                )

        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to insert verification token.",
                details={"op": "add", "table": "email_verification_tokens"},
            ) from e

    # -------------------------
    # READ
    # -------------------------
    @override
    def get_by_hash(self, token_hash: str) -> Optional[VerificationToken]:
        token_hash = Validation.require_str(token_hash, "token_hash")

        sql = text("""
                   SELECT id, account_id, token_hash, created_at, expires_at, used, used_at
                   FROM email_verification_tokens
                   WHERE token_hash = :token_hash
                   """)

        try:
            with self._db.connect() as conn:
                row = conn.execute(sql, {"token_hash": token_hash}).mappings().first()
                return None if row is None else self._map_to_token(row)
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch token by hash.",
                details={"op": "get_by_hash", "table": "email_verification_tokens"},
            ) from e

    @override
    def get_latest_by_account(self, account_id: int) -> Optional[VerificationToken]:
        account_id = Validation.require_int(account_id, "account_id")

        sql = text("""
                   SELECT id, account_id, token_hash, created_at, expires_at, used, used_at
                   FROM email_verification_tokens
                   WHERE account_id = :account_id
                   ORDER BY created_at DESC
                   LIMIT 1
                   """)

        try:
            with self._db.connect() as conn:
                row = conn.execute(sql, {"account_id": account_id}).mappings().first()
                return None if row is None else self._map_to_token(row)
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch latest token by account.",
                details={"op": "get_latest_by_account", "table": "email_verification_tokens"},
            ) from e

    # -------------------------
    # UPDATE
    # -------------------------
    @override
    def mark_used(self, token_id: int) -> None:
        token_id = Validation.require_int(token_id, "token_id")

        sql = text("""
                   UPDATE email_verification_tokens
                   SET used = TRUE, used_at = NOW()
                   WHERE id = :id
                   """)

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {"id": token_id})
                if int(result.rowcount or 0) == 0:
                    raise TokenNotFoundError(
                        message=f"Token not found for id: {token_id}",
                        details={"token_id": token_id},
                    )
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to mark token as used.",
                details={"op": "mark_used", "table": "email_verification_tokens"},
            ) from e

    # -------------------------
    # DELETE
    # -------------------------
    @override
    def clear_used_tokens(self, account_id: int) -> int:
        account_id = Validation.require_int(account_id, "account_id")

        sql = text("""
                   DELETE FROM email_verification_tokens
                   WHERE account_id = :account_id AND used = TRUE
                   """)

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {"account_id": account_id})
                return int(result.rowcount or 0)
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to delete used tokens.",
                details={"op": "clear_used_tokens", "table": "email_verification_tokens"},
            ) from e

    # -------------------------
    # HELPERS
    # -------------------------
    @staticmethod
    def _map_to_token(row) -> VerificationToken:
        """Convert a database row to a VerificationToken domain model."""
        return VerificationToken(
            account_id=row["account_id"],
            token_hash=row["token_hash"],
            expires_at=row["expires_at"],
            token_id=row["id"],
            created_at=row["created_at"],
            used=bool(row["used"]),
            used_at=row["used_at"],
        )
