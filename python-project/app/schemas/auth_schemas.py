from pydantic import BaseModel, EmailStr
from app.schemas.user_schemas import UserRead


class AuthRequest(BaseModel):
    id_token: str
    provider: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class PasswordLinkRequest(BaseModel):
    email: EmailStr
    password: str


class PasswordLoginRequest(BaseModel):
    email: EmailStr
    password: str
