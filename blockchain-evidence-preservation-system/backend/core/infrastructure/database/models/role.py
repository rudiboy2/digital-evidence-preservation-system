"""
Role ORM Model - RBAC roles for users.
"""
import uuid
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.infrastructure.database import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="role")

    def __repr__(self) -> str:
        return f"<Role name={self.name}>"


# Seeded roles
DEFAULT_ROLES = [
    {"name": "admin", "description": "Full system access"},
    {"name": "investigator", "description": "Can manage cases and upload evidence"},
    {"name": "officer", "description": "Can view and transfer evidence"},
    {"name": "analyst", "description": "Read-only access for analysis"},
    {"name": "auditor", "description": "Read-only access for compliance auditing"},
]
