from fastapi import APIRouter, Depends
from app.depends import get_auth_service, get_current_user
from app.schemas import AuthRequest, AuthResponse, PasswordLinkRequest, PasswordLoginRequest
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("", response_model=AuthResponse)
def auth_firebase(
    payload: AuthRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.authenticate_with_provider(payload.provider, payload.id_token)


@router.post("/password/link", response_model=AuthResponse)
def link_password(
    payload: PasswordLinkRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.link_password(current_user, payload.email, payload.password)


@router.post("/password/login", response_model=AuthResponse)
def login_password(
    payload: PasswordLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.login_with_password(payload.email, payload.password)
