from fastapi import APIRouter, Depends
from app.depends import get_auth_service, get_current_user
from app.schemas import AuthRequest, AuthResponse, PasswordLinkRequest, PasswordLoginRequest, RefreshTokenRequest, RefreshTokenResponse
from app.services.auth_service import AuthService
from app.models.user import User
from app.routing.docs import error_response

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "",
    response_model=AuthResponse,
    summary="Authenticate with provider",
    description="Authenticates user with OAuth provider token and returns access/refresh tokens.",
    responses={
        401: error_response(
            "INVALID_TOKEN",
            "Invalid token",
            "Invalid provider token. Possible codes: INVALID_TOKEN, TOKEN_EXPIRED, INVALID_TOKEN_AUDIENCE, INVALID_TOKEN_ISSUER, TOKEN_VERIFICATION_FAILED.",
        ),
        500: error_response(
            "FIREBASE_CONFIG_MISSING",
            "Firebase configuration missing. Please set FIREBASE_PROJECT_ID environment variable in your .env file.",
            "Server configuration error.",
        ),
        422: error_response("VALIDATION_ERROR", "Validation error", "Invalid request payload."),
    },
)
def auth_firebase(
    payload: AuthRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.authenticate_with_provider(payload.provider, payload.id_token)


@router.post(
    "/test/first",
    response_model=AuthResponse,
    summary="Authenticate test user",
    description="Authenticates or creates a hardcoded test user and returns access/refresh tokens.",
)
def auth_test_user(
    auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.authenticate_test_user()


@router.post(
    "/test/second",
    response_model=AuthResponse,
    summary="Authenticate test user 1",
    description="Authenticates or creates a second hardcoded test user and returns access/refresh tokens.",
)
def auth_test_user_1(
    auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.authenticate_test_user_1()


@router.post(
    "/password/link",
    response_model=AuthResponse,
    summary="Link password",
    description="Links email/password to the current user.",
    responses={
        401: error_response(
            "AUTH_HEADER_MISSING_OR_INVALID",
            "Authorization header missing or invalid",
            "Missing or invalid auth. Possible codes: AUTH_HEADER_MISSING_OR_INVALID, TOKEN_VALIDATION_FAILED, TOKEN_MISSING_SUB, INVALID_TOKEN_SUBJECT, USER_NOT_FOUND.",
        ),
        409: error_response("EMAIL_ALREADY_IN_USE", "Email already in use", "Email is already linked to another user."),
        422: error_response("VALIDATION_ERROR", "Validation error", "Invalid request payload."),
    },
)
def link_password(
    payload: PasswordLinkRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.link_password(current_user, payload.email, payload.password)


@router.post(
    "/password/login",
    response_model=AuthResponse,
    summary="Login with password",
    description="Authenticates user with email/password.",
    responses={
        401: error_response("INVALID_CREDENTIALS", "Invalid credentials", "Invalid email or password."),
        422: error_response("VALIDATION_ERROR", "Validation error", "Invalid request payload."),
    },
)
def login_password(
    payload: PasswordLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.login_with_password(payload.email, payload.password)


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh token",
    description="Creates a new access token using a refresh token.",
    responses={
        401: error_response(
            "INVALID_REFRESH_TOKEN",
            "Invalid refresh token",
            "Invalid or expired refresh token. Possible codes: INVALID_REFRESH_TOKEN, TOKEN_MISSING_SUB, USER_NOT_FOUND.",
        ),
        422: error_response("VALIDATION_ERROR", "Validation error", "Invalid request payload."),
    },
)
def refresh_token(
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Обновляет access токен используя refresh токен."""
    return auth_service.refresh_token(payload.refresh_token)
