"""
User Repository - Data access layer for user records.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional
from uuid import UUID

from core.infrastructure.database.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.role))
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User)
            .where(User.email == email)
            .options(selectinload(User.role))
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> User:
        user = User(**kwargs)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: UUID, **kwargs) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        for key, value in kwargs.items():
            setattr(user, key, value)
        await self.db.flush()
        return user
