# src/errors.py
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
    DB is reachable but the query fails (syntax, constraint, etc.)
    Usually it's a server bug -> 500.
    """

    code: str = "DB_QUERY_ERROR"
    status_code: int = 500


@dataclass
class DomainError(AppError):
    code: str = "DOMAIN_ERROR"
    status_code: int = 400


@dataclass
class ValidationError(DomainError):
    code: str = "VALIDATION_ERROR"
    status_code: int = 422


@dataclass
class ConflictError(DomainError):
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


# -----------------------------
# Account-specific errors (domain layer friendly)
# -----------------------------
@dataclass
class ConfigurationError(InfrastructureError):
    code: str = "CONFIGURATION_ERROR"
    status_code: int = 500


@dataclass
class AccountError(DomainError):
    code: str = "ACCOUNT_ERROR"
    status_code: int = 400


@dataclass
class AccountNotFoundError(AccountError):
    code: str = "ACCOUNT_NOT_FOUND"
    status_code: int = 404


@dataclass
class AccountAlreadyExistsError(AccountError):
    code: str = "ACCOUNT_ALREADY_EXISTS"
    status_code: int = 409


# -----------------------------
# Email Verification Token errors
# -----------------------------
@dataclass
class TokenError(DomainError):
    code: str = "TOKEN_ERROR"
    status_code: int = 400


@dataclass
class TokenNotFoundError(TokenError):
    code: str = "TOKEN_NOT_FOUND"
    status_code: int = 404


@dataclass
class TokenExpiredError(TokenError):
    code: str = "TOKEN_EXPIRED"
    status_code: int = 400


@dataclass
class TokenAlreadyUsedError(TokenError):
    code: str = "TOKEN_ALREADY_USED"
    status_code: int = 400


@dataclass
class EmailVerificationError(TokenError):
    code: str = "EMAIL_VERIFICATION_ERROR"
    status_code: int = 400


# -----------------------------
# Listing-specific errors (domain layer friendly)
# -----------------------------
@dataclass
class ListingError(DomainError):
    code: str = "LISTING_ERROR"
    status_code: int = 400


@dataclass
class ListingNotFoundError(ListingError):
    code: str = "LISTING_NOT_FOUND"
    status_code: int = 404


# -----------------------------
# Comment-specific errors (domain layer friendly)
# -----------------------------
@dataclass
class CommentError(DomainError):
    code: str = "COMMENT_ERROR"
    status_code: int = 400


@dataclass
class CommentNotFoundError(CommentError):
    code: str = "COMMENT_NOT_FOUND"
    status_code: int = 404


# -----------------------------
# Rating-specific errors (domain layer friendly)
# -----------------------------


@dataclass
class RatingError(DomainError):
    code: str = "RATING_ERROR"
    status_code: int = 400

@dataclass
class RatingNotFoundError(RatingError):
    code: str = "RATING_NOT_FOUND"
    status_code: int = 404


# -----------------------------
# Offer-specific errors (domain layer friendly)
# -----------------------------
@dataclass
class OfferError(DomainError):
    code: str = "OFFER_ERROR"
    status_code: int = 400


@dataclass
class OfferNotFoundError(OfferError):
    code: str = "OFFER_NOT_FOUND"
    status_code: int = 404



# -----------------------------
# minio-specific errors (domain layer friendly)
# -----------------------------

@dataclass
class StorageError(InfrastructureError):
    """
    Base class for storage-related infrastructure failures.
    Example: MinIO unreachable, bad credentials, network error.
    """
    code: str = "STORAGE_ERROR"
    status_code: int = 503


@dataclass
class StorageUnavailableError(StorageError):
    """
    Object storage service is down or unreachable.
    Maps to 503.
    """
    code: str = "STORAGE_UNAVAILABLE"
    status_code: int = 503

@dataclass
class MediaNotFoundError(DomainError):
    """
    Requested media object does not exist in storage.
    Maps to 404.
    """
    code: str = "MEDIA_NOT_FOUND"
    status_code: int = 404


@dataclass
class MediaConflictError(DomainError):
    """
    Used if you want to signal overwrite conflicts or duplicate uploads.
    Optional — include only if needed.
    """
    code: str = "MEDIA_CONFLICT"
    status_code: int = 409