"""
Evidence ORM Model
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Text, BigInteger, Integer, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.infrastructure.database import Base
from core.domain.evidence import EvidenceStatus, EvidenceType


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_type: Mapped[str] = mapped_column(
        SAEnum(EvidenceType, values_callable=lambda x: [e.value for e in x]),
        default=EvidenceType.OTHER.value,
        nullable=False,
    )
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    ipfs_cid: Mapped[str] = mapped_column(String(100), nullable=True)
    blockchain_tx_hash: Mapped[str] = mapped_column(String(66), nullable=True, index=True)
    blockchain_block_number: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        SAEnum(EvidenceStatus, values_callable=lambda x: [e.value for e in x]),
        default=EvidenceStatus.PENDING.value,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="evidence")
    uploader: Mapped["User"] = relationship(
        "User", back_populates="evidence_uploaded", foreign_keys=[uploaded_by]
    )
    custody_logs: Mapped[list["CustodyLog"]] = relationship(
        "CustodyLog", back_populates="evidence", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Evidence id={self.id} file_name={self.file_name} status={self.status}>"
