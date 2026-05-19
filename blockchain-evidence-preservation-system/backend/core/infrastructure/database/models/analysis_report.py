"""
AnalysisReport ORM Model - Extended with Tanzania TDFL-STD-2023 mandatory fields.
All fields required for court-admissible forensic reports in Tanzania 2026.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.infrastructure.database import Base


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True)
    submitted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Core report content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    findings: Mapped[str] = mapped_column(Text, nullable=True)
    methodology: Mapped[str] = mapped_column(Text, nullable=True)
    conclusion: Mapped[str] = mapped_column(Text, nullable=True)
    evidence_ids: Mapped[str] = mapped_column(Text, nullable=True)

    # ── ANALYST UNIQUE FIELDS (TDFL-STD-2023) ─────────────────────────────
    # Analyst certification (TCRA-certified examiner number)
    analyst_certification_number: Mapped[str] = mapped_column(String(100), nullable=True)

    # Forensic tools used (required for court admissibility)
    forensic_tool_name: Mapped[str] = mapped_column(String(200), nullable=True)
    # e.g. "Autopsy, Cellebrite UFED, FTK Imager"
    forensic_tool_version: Mapped[str] = mapped_column(String(100), nullable=True)
    # e.g. "Autopsy 4.21.0, Cellebrite UFED 7.68"

    # Tanzania Digital Forensics Lab reference number
    lab_reference_number: Mapped[str] = mapped_column(String(100), nullable=True)

    # Examination timeline
    examination_start_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    examination_end_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Forensic copy hash (work copy — separate from original)
    work_copy_hash: Mapped[str] = mapped_column(String(64), nullable=True)

    # Statement of independence (no conflict of interest)
    independence_statement: Mapped[bool] = mapped_column(Boolean, default=False)
    independence_statement_text: Mapped[str] = mapped_column(Text, nullable=True)

    # Number of evidence copies made and their locations
    copies_made: Mapped[int] = mapped_column(nullable=True)
    copies_location: Mapped[str] = mapped_column(Text, nullable=True)

    # Expert witness designation
    is_expert_witness: Mapped[bool] = mapped_column(Boolean, default=False)
    expert_witness_court_designation: Mapped[str] = mapped_column(String(255), nullable=True)

    # Digital signature / analyst declaration
    analyst_declaration: Mapped[str] = mapped_column(Text, nullable=True)

    # File attachment (PDF report upload)
    report_file_path: Mapped[str] = mapped_column(String(1000), nullable=True)
    report_file_name: Mapped[str] = mapped_column(String(500), nullable=True)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    blockchain_tx_hash: Mapped[str] = mapped_column(String(66), nullable=True)

    # Status: draft | submitted | reviewed | court_accepted | court_rejected
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="analysis_reports")
    analyst: Mapped["User"] = relationship("User", foreign_keys=[submitted_by])

    def __repr__(self) -> str:
        return f"<AnalysisReport id={self.id} case_id={self.case_id}>"
