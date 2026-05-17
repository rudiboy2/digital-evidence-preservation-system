"""
AnalysisReport ORM Model - Forensic analysis reports submitted by analysts.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.infrastructure.database import Base


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True
    )
    submitted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    findings: Mapped[str] = mapped_column(Text, nullable=True)
    methodology: Mapped[str] = mapped_column(Text, nullable=True)
    conclusion: Mapped[str] = mapped_column(Text, nullable=True)
    # Optional link to specific evidence items (comma-separated UUIDs)
    evidence_ids: Mapped[str] = mapped_column(Text, nullable=True)
    # File attachment (if analyst uploads a PDF report)
    report_file_path: Mapped[str] = mapped_column(String(1000), nullable=True)
    report_file_name: Mapped[str] = mapped_column(String(500), nullable=True)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    blockchain_tx_hash: Mapped[str] = mapped_column(String(66), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="draft", nullable=False
    )  # draft | submitted | reviewed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="analysis_reports")
    analyst: Mapped["User"] = relationship("User", foreign_keys=[submitted_by])

    def __repr__(self) -> str:
        return f"<AnalysisReport id={self.id} case_id={self.case_id}>"
