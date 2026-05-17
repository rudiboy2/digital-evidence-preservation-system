"""
Auth Service - Handles user authentication, password hashing, and JWT issuance.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from typing import Optional
from uuid import UUID

from core.infrastructure.database import get_db
from core.infrastructure.database.repositories.user_repository import UserRepository
from core.infrastructure.database.models.role import Role
from core.infrastructure.database.models.user import User
from config.schemas import UserCreateRequest
from config.settings import settings
from security.jwt_handler import JWTHandler

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=settings.BCRYPT_ROUNDS)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    def hash_password(self, plain_password: str) -> str:
        return pwd_context.hash(plain_password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        return await self.user_repo.get_by_email(email)

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        return await self.user_repo.get_by_id(UUID(user_id))

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    async def create_user(self, user_data: UserCreateRequest) -> User:
        from sqlalchemy import select
        # Resolve role
        role_result = await self.db.execute(
            __import__("sqlalchemy", fromlist=["select"]).select(Role).where(
                Role.name == user_data.role_name
            )
        )
        role = role_result.scalar_one_or_none()
        if not role:
            raise ValueError(f"Role '{user_data.role_name}' does not exist.")

        hashed_pw = self.hash_password(user_data.password)
        user = await self.user_repo.create(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_pw,
            badge_number=user_data.badge_number,
            department=user_data.department,
            role_id=role.id,
            is_active=True,
        )
        return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency that validates the JWT and returns the current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    jwt_handler = JWTHandler()
    payload = jwt_handler.verify_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    return user
