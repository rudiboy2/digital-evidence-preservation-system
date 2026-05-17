"""
Authentication Router - Handles user authentication and token management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from core.infrastructure.database import get_db
from security.auth_service import AuthService, get_current_user
from security.jwt_handler import JWTHandler
from config.schemas import (
    UserCreateRequest,
    UserResponse,
    TokenResponse,
    TokenRefreshRequest,
)
from core.infrastructure.database.models.user import User

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    user_data: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account. Requires admin approval for sensitive roles."""
    auth_service = AuthService(db)

    existing = await auth_service.get_user_by_email(user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    user = await auth_service.create_user(user_data)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and obtain JWT tokens",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Authenticate a user and return access + refresh JWT tokens."""
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled.",
        )

    jwt_handler = JWTHandler()
    access_token = jwt_handler.create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.name}
    )
    refresh_token = jwt_handler.create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh_token(
    token_request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Use a valid refresh token to obtain a new access token."""
    jwt_handler = JWTHandler()
    payload = jwt_handler.verify_refresh_token(token_request.refresh_token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
        )

    access_token = jwt_handler.create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.name}
    )
    new_refresh_token = jwt_handler.create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve the profile of the currently authenticated user."""
    return current_user


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout (invalidate refresh token)",
)
async def logout(
    token_request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Invalidate the provided refresh token (server-side blacklist)."""
    jwt_handler = JWTHandler()
    await jwt_handler.blacklist_token(token_request.refresh_token, db)
