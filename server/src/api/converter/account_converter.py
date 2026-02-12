from pydantic import BaseModel, EmailStr


class AccountSignup(BaseModel):
    email: EmailStr
    password: str
    fname: str
    lname: str


class AccountResponse(BaseModel):
    email: EmailStr
    fname: str
    lname: str
