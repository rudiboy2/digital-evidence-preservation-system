"""
Case Domain Entity - Represents an investigation/legal case.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4


class CaseStatus(str, Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    CLOSED = "closed"
    ARCHIVED = "archived"


class CasePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Case:
    """Core domain entity representing an investigation case."""

    id: UUID = field(default_factory=uuid4)
    case_number: str = field(default="")
    title: str = field(default="")
    description: str = field(default="")
    status: CaseStatus = field(default=CaseStatus.OPEN)
    priority: CasePriority = field(default=CasePriority.MEDIUM)
    created_by: UUID = field(default=None)
    assigned_officers: List[UUID] = field(default_factory=list)
    jurisdiction: str = field(default="")
    incident_date: Optional[datetime] = field(default=None)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = field(default=None)
    closed_by: Optional[UUID] = field(default=None)

    def close(self, closed_by: UUID):
        """Close this case."""
        self.status = CaseStatus.CLOSED
        self.closed_at = datetime.utcnow()
        self.closed_by = closed_by
        self.updated_at = datetime.utcnow()

    def reopen(self):
        """Re-open a closed case."""
        if self.status == CaseStatus.ARCHIVED:
            raise ValueError("Cannot re-open an archived case.")
        self.status = CaseStatus.OPEN
        self.closed_at = None
        self.closed_by = None
        self.updated_at = datetime.utcnow()

    def is_editable(self) -> bool:
        """Only open and under_review cases can be edited."""
        return self.status in (CaseStatus.OPEN, CaseStatus.UNDER_REVIEW)

    @classmethod
    def generate_case_number(cls, prefix: str = "BEPS") -> str:
        """Generate a unique case number with a prefix and timestamp."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        short_id = str(uuid4()).split("-")[0].upper()
        return f"{prefix}-{timestamp}-{short_id}"
