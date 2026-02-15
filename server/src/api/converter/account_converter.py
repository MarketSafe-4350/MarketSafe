from pydantic import BaseModel, EmailStr


class AccountSignup(BaseModel):
    """Data model for account signup request."""

    email: EmailStr
    password: str
    fname: str
    lname: str


class AccountResponse(BaseModel):
    """Data model for account response."""

    email: EmailStr
    fname: str
    lname: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"