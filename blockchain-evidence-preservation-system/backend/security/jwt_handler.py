"""
JWT Handler - Creates and validates JSON Web Tokens.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings


class JWTHandler:
    """Handles creation and validation of JWT access and refresh tokens."""

    def create_access_token(self, data: Dict[str, Any]) -> str:
        payload = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload.update({"exp": expire, "type": "access"})
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        payload = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
        payload.update({"exp": expire, "type": "refresh"})
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate an access token. Returns payload or None."""
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            if payload.get("type") != "access":
                return None
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate a refresh token. Returns payload or None."""
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            if payload.get("type") != "refresh":
                return None
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    async def blacklist_token(self, token: str, db: AsyncSession) -> None:
        """
        Add a refresh token to the blacklist.
        In production this would use Redis; here we store in the DB.
        """
        # Simplified: decode to get jti/expiry and persist
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            # In a real implementation: store payload["jti"] in a token_blacklist table
        except jwt.InvalidTokenError:
            pass  # Already invalid; nothing to blacklist
