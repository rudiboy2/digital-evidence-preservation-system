"""
User ORM Model
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.infrastructure.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    badge_number: Mapped[str] = mapped_column(String(50), nullable=True)
    department: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_login_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="selectin")
    evidence_uploaded: Mapped[list["Evidence"]] = relationship(
        "Evidence", back_populates="uploader", foreign_keys="Evidence.uploaded_by"
    )
    custody_logs: Mapped[list["CustodyLog"]] = relationship(
        "CustodyLog", back_populates="officer", foreign_keys="CustodyLog.performed_by"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
