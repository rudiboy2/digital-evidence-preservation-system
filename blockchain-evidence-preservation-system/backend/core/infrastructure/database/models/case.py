"""
Case ORM Model - Extended with analyst assignments and reports.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum, Table, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.infrastructure.database import Base
from core.domain.case import CaseStatus, CasePriority

# Association: case <-> officer assignments (officers who can upload evidence)
case_officer_association = Table(
    "case_officer_assignments",
    Base.metadata,
    Column("case_id", UUID(as_uuid=True), ForeignKey("cases.id"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
)

# Association: case <-> analyst assignments
case_analyst_association = Table(
    "case_analyst_assignments",
    Base.metadata,
    Column("case_id", UUID(as_uuid=True), ForeignKey("cases.id"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
)


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_number: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        SAEnum(CaseStatus, values_callable=lambda x: [e.value for e in x]),
        default=CaseStatus.OPEN.value, nullable=False,
    )
    priority: Mapped[str] = mapped_column(
        SAEnum(CasePriority, values_callable=lambda x: [e.value for e in x]),
        default=CasePriority.MEDIUM.value, nullable=False,
    )
    jurisdiction: Mapped[str] = mapped_column(String(255), nullable=True)
    incident_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Created by investigator
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    closed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    closed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    closer:  Mapped["User"] = relationship("User", foreign_keys=[closed_by])

    # Officers assigned to upload evidence to this case
    assigned_officers: Mapped[list["User"]] = relationship(
        "User", secondary=case_officer_association,
        primaryjoin="Case.id == case_officer_assignments.c.case_id",
        secondaryjoin="User.id == case_officer_assignments.c.user_id",
    )

    # Analysts assigned to perform forensic analysis
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
        from core.domain.case import CaseStatus
        return self.status in (CaseStatus.OPEN.value, CaseStatus.UNDER_REVIEW.value)

    def __repr__(self) -> str:
        return f"<Case case_number={self.case_number} status={self.status}>"
