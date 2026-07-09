"""Auth request/response schemas."""

from pydantic import EmailStr, Field

from app.core.schemas import NAME_MAX, SanitizedModel


class RegisterRequest(SanitizedModel):
    business_name: str = Field(min_length=2, max_length=NAME_MAX)
    full_name: str = Field(min_length=2, max_length=NAME_MAX)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)


class LoginRequest(SanitizedModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(SanitizedModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 — OAuth2 token type, not a secret
    expires_in: int  # seconds
