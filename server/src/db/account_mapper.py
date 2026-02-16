from __future__ import annotations

from typing import Any, Mapping

from src.domain_models import Account


class AccountMapper:
    """
    Responsible for converting DB rows/dicts into Account objects.

    Keep all mapping logic here so the DB implementation stays clean.

    NOTE:
    All SELECT queries must use:
        result.mappings().first()
        result.mappings().all()
    So this class never touches SQLAlchemy internals.
    """

    # @staticmethod
    # def from_row(row: Any) -> Account:
    #     """
    #     Accepts an SQLAlchemy Row (row._mapping)
    #     """
    #     m: Mapping[str, Any] = row._mapping  # SQLAlchemy Row -> mapping view
    #     return AccountMapper.from_mapping(m)

    @staticmethod
    def from_mapping(m: Mapping[str, Any]) -> Account:
        """
        Accepts a dict-like mapping with keys:
        id, email, password, fname, lname, verified
        """
        return Account(
            account_id=int(m["id"]),
            email=str(m["email"]),
            password=str(m["password"]),
            fname=str(m["fname"]),
            lname=str(m["lname"]),
            verified=bool(m["verified"]),
        )


