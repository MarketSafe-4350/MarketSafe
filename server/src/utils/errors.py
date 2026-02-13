from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class AppError(Exception):
    """
    Base error for your application.

    - message: human-readable
    - code: stable internal code (good for frontend + logs)
    - status_code: HTTP mapping (used by API layer)
    - details: optional extra fields (safe, non-sensitive)
    """
    message: str
    code: str = "APP_ERROR"
    status_code: int = 500
    details: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return self.message

@dataclass
class InfrastructureError(AppError):
    code: str = "INFRA_ERROR"
    status_code: int = 503


@dataclass
class DatabaseUnavailableError(InfrastructureError):
    code: str = "DB_UNAVAILABLE"
    status_code: int = 503


@dataclass
class DatabaseQueryError(InfrastructureError):
    """
    Use this when DB is reachable but the query fails (syntax, constraint, etc.)
    Usually it's a server bug -> 500.
    """
    code: str = "DB_QUERY_ERROR"
    status_code: int = 500

# -----------------------------
# Domain/Business rule errors (unapproved behaviors)
# -----------------------------

@dataclass
class DomainError(AppError):
    code: str = "DOMAIN_ERROR"
    status_code: int = 400



@dataclass
class ValidationError(DomainError):
    """
    Input is invalid (missing fields, wrong format).
    """
    code: str = "VALIDATION_ERROR"
    status_code: int = 422

@dataclass
class ConflictError(DomainError):
    """
    Conflicts like duplicate unique fields, state conflict, etc.
    """
    code: str = "CONFLICT"
    status_code: int = 409


@dataclass
class UnapprovedBehaviorError(DomainError):
    """
    Used when a user tries an action that is not allowed by the business rules.
    Example: buyer tries to rate their own listing.
    """
    code: str = "UNAPPROVED_BEHAVIOR"
    status_code: int = 403