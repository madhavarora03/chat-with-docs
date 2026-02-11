from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from starlette.status import HTTP_201_CREATED, HTTP_401_UNAUTHORIZED, HTTP_409_CONFLICT

from app.core import security
from app.exceptions import (
    DuplicateEmailError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserNotFoundError,
)
from app.models import User
from app.schemas import (
    LoginRequest,
    LogoutResponse,
    SignupRequest,
    SignupResponse,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService, get_auth_service, get_current_user
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserResponse)
def get_user(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/token", response_model=TokenResponse, include_in_schema=False)
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        access_token, refresh_token = auth_service.login(
            form_data.username, form_data.password
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    security.set_refresh_token_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
def login_with_body(
    credentials: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        access_token, refresh_token = auth_service.login(
            credentials.email, credentials.password
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    security.set_refresh_token_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/signup", response_model=SignupResponse, status_code=HTTP_201_CREATED)
def signup(
    payload: SignupRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> SignupResponse:
    try:
        user = auth_service.create_user(
            email=payload.email,
            name=payload.name,
            password=payload.password,
        )
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail=exc.message) from exc

    access_token = auth_service.create_access_token(user)
    refresh_token = auth_service.issue_refresh_token(user)
    security.set_refresh_token_cookie(response, refresh_token)
    logger.info("Signup successful for user_id=%s", user.id)
    return SignupResponse(
        user=UserResponse.model_validate(user),
        token=TokenResponse(access_token=access_token),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        logger.warning("Refresh attempt with missing cookie")
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        access_token, new_refresh_token = auth_service.refresh_tokens(refresh_token)
    except (InvalidTokenError, UserNotFoundError) as exc:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    security.set_refresh_token_cookie(response, new_refresh_token)
    logger.info("Tokens rotated successfully")
    return TokenResponse(access_token=access_token)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    response: Response,
    user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> LogoutResponse:
    revoked = auth_service.revoke_all_user_tokens(user.id)
    logger.info("Logout: revoked %d refresh tokens for user_id=%s", revoked, user.id)
    response.delete_cookie(key="refresh_token", path="/api/v1/auth")
    return LogoutResponse()
