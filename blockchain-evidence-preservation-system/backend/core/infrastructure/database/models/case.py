"""
Case ORM Model - Extended with Tanzania 2026 legal compliance fields.
Includes warrant tracking, court status, DPP reference, OB number.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum, Table, Column, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.infrastructure.database import Base
from core.domain.case import CaseStatus, CasePriority

case_officer_association = Table(
    "case_officer_assignments", Base.metadata,
    Column("case_id", UUID(as_uuid=True), ForeignKey("cases.id"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
)

case_analyst_association = Table(
    "case_analyst_assignments", Base.metadata,
    Column("case_id", UUID(as_uuid=True), ForeignKey("cases.id"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
)


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), default=CaseStatus.OPEN.value, nullable=False
    )
    priority: Mapped[str] = mapped_column(
        String(20), default=CasePriority.MEDIUM.value, nullable=False
    )
    jurisdiction: Mapped[str] = mapped_column(String(255), nullable=True)
    incident_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # ── INVESTIGATOR UNIQUE FIELDS ──────────────────────────────────────────
    # Legal authority to collect evidence (Tanzania Criminal Procedure Act Cap 20)
    warrant_number: Mapped[str] = mapped_column(String(100), nullable=True)
    warrant_issuing_court: Mapped[str] = mapped_column(String(255), nullable=True)
    warrant_issue_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    warrant_expiry_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Occurrence Book entry number (TPF OB)
    ob_number: Mapped[str] = mapped_column(String(100), nullable=True)

    # DPP Office reference (Director of Public Prosecutions)
    dpp_reference_number: Mapped[str] = mapped_column(String(100), nullable=True)

    # Court tracking
    court_name: Mapped[str] = mapped_column(String(255), nullable=True)
    court_case_number: Mapped[str] = mapped_column(String(100), nullable=True)
    next_hearing_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    court_status: Mapped[str] = mapped_column(String(50), nullable=True)
    # under_investigation | report_submitted | forwarded_to_dpp |
    # charges_filed | before_court | judgment_delivered | archived

    # Inter-agency tracking
    referring_agency: Mapped[str] = mapped_column(String(100), nullable=True)
    # TPF | PCCB | TCRA | FIU | INTERPOL
    external_reference: Mapped[str] = mapped_column(String(100), nullable=True)

    # Evidence submitted to court flag
    evidence_submitted_to_court: Mapped[bool] = mapped_column(Boolean, default=False)
    evidence_submitted_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # ── STANDARD FIELDS ────────────────────────────────────────────────────
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    closed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    closer:  Mapped["User"] = relationship("User", foreign_keys=[closed_by])
    assigned_officers: Mapped[list["User"]] = relationship(
        "User", secondary=case_officer_association,
        primaryjoin="Case.id == case_officer_assignments.c.case_id",
        secondaryjoin="User.id == case_officer_assignments.c.user_id",
    )
    assigned_analysts: Mapped[list["User"]] = relationship(
        "User", secondary=case_analyst_association,
        primaryjoin="Case.id == case_analyst_assignments.c.case_id",
        secondaryjoin="User.id == case_analyst_assignments.c.user_id",
    )
    evidence: Mapped[list["Evidence"]] = relationship(
        "Evidence", back_populates="case", cascade="all, delete-orphan"
    )
    analysis_reports: Mapped[list["AnalysisReport"]] = relationship(
        "AnalysisReport", back_populates="case", cascade="all, delete-orphan"
    )

    def is_editable(self) -> bool:
        return self.status in (CaseStatus.OPEN.value, CaseStatus.UNDER_REVIEW.value, "under_investigation")

    def __repr__(self) -> str:
        return f"<Case case_number={self.case_number} status={self.status}>"
