"""
CustodyLog ORM Model - Extended immutable chain-of-custody entries.
Tracks every action: upload, view, download, assignment, analysis, report submission.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.infrastructure.database import Base


class CustodyLog(Base):
    __tablename__ = "custody_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Core references
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=True, index=True
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True, index=True
    )
    # Who did what
    performed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    performed_by_role: Mapped[str] = mapped_column(String(50), nullable=True)
    # Action details
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    # upload | view | download | assignment | analysis | report_submission
    # transfer | verify | access | custody_transfer
    from_officer: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    to_officer: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    location: Mapped[str] = mapped_column(String(500), nullable=True)
    # IP address for audit trail
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    # Blockchain
    blockchain_tx_hash: Mapped[str] = mapped_column(String(66), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    evidence: Mapped["Evidence"] = relationship("Evidence", back_populates="custody_logs")
    officer: Mapped["User"] = relationship(
        "User", back_populates="custody_logs", foreign_keys=[performed_by]
    )

    def __repr__(self) -> str:
        return f"<CustodyLog id={self.id} action={self.action}>"
