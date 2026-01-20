from pydantic import BaseModel, EmailStr, Field
from app.schemas.user_schemas import UserRead


class AuthRequest(BaseModel):
    id_token: str
    provider: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead

class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str

class PasswordLinkRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class PasswordLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
