from pydantic import BaseModel, EmailStr
from typing import Optional


class AccountSignup(BaseModel):
    """Data model for account signup request."""

    email: EmailStr
    password: str
    fname: str
    lname: str


class AccountResponse(BaseModel):
    """Data model for account response."""

    id: Optional[int] = None
    email: EmailStr
    fname: str
    lname: str
    verified: bool
    average_rating_received: Optional[float] = None
    sum_of_ratings_received: int
    rating_count: int


class SignupResponse(BaseModel):
    """Data model for signup response with verification link."""

    email: EmailStr
    fname: str
    lname: str
    verification_link: str


class VerifyEmailResponse(BaseModel):
    """Data model for email verification response."""

    email: EmailStr
    fname: str
    lname: str
    verified: bool
    message: str = "Email verified successfully!"


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str
