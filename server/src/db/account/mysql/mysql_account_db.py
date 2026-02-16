"""
NOTE:
Connection-level errors (OperationalError) are handled in DBUtility
and converted into DatabaseUnavailableError.

This class only handles query-level failures.
"""
from __future__ import annotations
from typing import Optional, List

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing_extensions import override

from src.db import DBUtility, AccountMapper
from src.db.account import AccountDB
from src.domain_models import Account
from src.utils import (Validation, AccountAlreadyExistsError, DatabaseQueryError, AccountNotFoundError)


class MySQLAccountDB(AccountDB):
    def __init__(self, db: DBUtility) -> None:
        super().__init__(db)

    # -----------------------------
    # CREATE
    # -----------------------------
    @override
    def add(self, account: Account) -> Account:
        Validation.require_not_none(account, "account")

        sql = text("""
                   INSERT INTO account (email, password, fname, lname, verified)
                   VALUES (:email, :password, :fname, :lname, :verified)
                   """)

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {
                    "email": account.email,
                    "password": account.password,
                    "fname": account.fname.strip(),
                    "lname": account.lname.strip(),
                    "verified": bool(account.verified),
                })

                new_id = int(result.lastrowid)

                # INSERT doesn't return a row -> we return what we inserted + generated id
                return Account(

                    email=account.email,
                    password=account.password,
                    fname=account.fname.strip(),
                    lname=account.lname.strip(),
                    verified=bool(account.verified),
                    account_id=new_id,
                )

        except IntegrityError as e:
            # Unique email violation (or other constraint)
            raise AccountAlreadyExistsError(
                message=f"Account already exists for email: {account.email}",
                details={"email": account.email},
            ) from e
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to insert account.",
                details={"op": "add", "table": "account"},
            ) from e

    # -----------------------------
    # READ
    # -----------------------------
    @override
    def get_by_id(self, account_id: int) -> Optional[Account]:
        Validation.require_int(account_id, "account_id")

        sql = text("""
                   SELECT id, email, password, fname, lname, verified
                   FROM account
                   WHERE id = :id
                   """)

        try:
            with self._db.connect() as conn:
                row = conn.execute(sql, {"id": account_id}).mappings().first()
                return None if row is None else AccountMapper.from_mapping(row)
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch account by id.",
                details={"op": "get_by_id", "table": "account"},
            ) from e

    @override
    def get_by_email(self, email: str) -> Optional[Account]:
        email = Validation.valid_email(email)

        sql = text("""
                   SELECT id, email, password, fname, lname, verified
                   FROM account
                   WHERE email = :email
                   """)

        try:
            with self._db.connect() as conn:
                row = conn.execute(sql, {"email": email}).mappings().first()
                return None if row is None else AccountMapper.from_mapping(row)
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch account by email.",
                details={"op": "get_by_email", "table": "account"},
            ) from e

    @override
    def get_all(self) -> List[Account]:
        sql = text("""
                   SELECT id, email, password, fname, lname, verified
                   FROM account
                   ORDER BY id ASC
                   """)

        try:
            with self._db.connect() as conn:
                rows = conn.execute(sql).mappings().all()
                return [AccountMapper.from_mapping(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to fetch accounts.",
                details={"op": "get_all", "table": "account"},
            ) from e

    # -----------------------------
    # UPDATE
    # -----------------------------
    @override
    def set_verified(self, account_id: int, verified: bool) -> None:
        Validation.require_int(account_id, "account_id")
        Validation.is_boolean(verified, "verified")

        sql = text("""
                   UPDATE account
                   SET verified = :verified
                   WHERE id = :id
                   """)

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {"verified": bool(verified), "id": account_id})
                if int(result.rowcount or 0) == 0:
                    # CONTRACT: must raise if missing
                    raise AccountNotFoundError(
                        message=f"Account not found for id: {account_id}",
                        details={"account_id": account_id},
                    )
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to update account verification.",
                details={"op": "set_verified", "table": "account"},
            ) from e

    @override
    def set_verified_by_email(self, email: str, verified: bool) -> None:
        email = Validation.valid_email(email)
        Validation.is_boolean(verified, "verified")

        sql = text("""
                   UPDATE account
                   SET verified = :verified
                   WHERE email = :email
                   """)

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {"verified": bool(verified), "email": email})
                if int(result.rowcount or 0) == 0:
                    raise AccountNotFoundError(
                        message=f"Account not found for email: {email}",
                        details={"email": email},
                    )
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to update account verification by email.",
                details={"op": "set_verified_by_email", "table": "account"},
            ) from e

    # -----------------------------
    # DELETE
    # -----------------------------
    @override
    def remove(self, account_id: int) -> bool:
        Validation.require_int(account_id, "account_id")

        sql = text("""
                   DELETE
                   FROM account
                   WHERE id = :id
                   """)

        try:
            with self._db.transaction() as conn:
                result = conn.execute(sql, {"id": account_id})
                return (result.rowcount or 0) > 0
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to delete account.",
                details={"op": "remove", "table": "account"},
            ) from e

    # -----------------------------
    # TEST / DEV
    # -----------------------------
    @override
    def clear_db(self) -> None:
        sql = text("DELETE FROM account")

        try:
            with self._db.transaction() as conn:
                conn.execute(sql)
        except SQLAlchemyError as e:
            raise DatabaseQueryError(
                message="Failed to clear account table.",
                details={"op": "clear_db", "table": "account"},
            ) from e
