"""
Pydantic Schemas - Complete request/response models aligned with core workflow.
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime


# ---------------------------------------------------------------------------
# Auth / User
# ---------------------------------------------------------------------------

class UserCreateRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=12)
    badge_number: Optional[str] = None
    department: Optional[str] = None
    role_name: str = Field(default="officer")


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    full_name: str
    badge_number: Optional[str] = None
    department: Optional[str] = None
    is_active: bool
    created_at: datetime
    role: Optional[RoleResponse] = None


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    refresh_token: str


# ---------------------------------------------------------------------------
# Case
# ---------------------------------------------------------------------------

class CaseCreateRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    description: Optional[str] = None
    priority: str = Field(default="medium")
    jurisdiction: Optional[str] = None
    incident_date: Optional[datetime] = None


class CaseUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=500)
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    jurisdiction: Optional[str] = None


class CaseAssignRequest(BaseModel):
    user_id: UUID
    role: str = Field(..., description="officer or analyst")


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    case_number: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    jurisdiction: Optional[str] = None
    incident_date: Optional[datetime] = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    assigned_officers: List[UserResponse] = []
    assigned_analysts: List[UserResponse] = []


class CaseListResponse(BaseModel):
    items: List[CaseResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

class EvidenceCreateRequest(BaseModel):
    case_id: UUID
    description: Optional[str] = None


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    case_id: UUID
    uploaded_by: UUID
    file_name: str
    file_size: int
    mime_type: str
    evidence_type: str
    sha256_hash: str
    ipfs_cid: Optional[str] = None
    blockchain_tx_hash: Optional[str] = None
    blockchain_block_number: Optional[int] = None
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class EvidenceListResponse(BaseModel):
    items: List[EvidenceResponse]
    total: int
    page: int
    page_size: int
    pages: int


class EvidenceVerificationResponse(BaseModel):
    evidence_id: str
    is_valid: bool
    db_hash: str
    computed_hash: Optional[str] = None
    blockchain_hash: Optional[str] = None
    blockchain_tx_hash: Optional[str] = None
    status: str
    message: str


# ---------------------------------------------------------------------------
# Custody / Audit Log
# ---------------------------------------------------------------------------

class CustodyTransferRequest(BaseModel):
    to_officer_id: UUID
    notes: Optional[str] = None
    location: Optional[str] = None


class CustodyLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    evidence_id: Optional[UUID] = None
    case_id: Optional[UUID] = None
    action: str
    performed_by: UUID
    performed_by_role: Optional[str] = None
    from_officer: Optional[UUID] = None
    to_officer: Optional[UUID] = None
    notes: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    blockchain_tx_hash: Optional[str] = None
    timestamp: datetime


class AuditLogListResponse(BaseModel):
    items: List[CustodyLogResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ---------------------------------------------------------------------------
# Analysis Report
# ---------------------------------------------------------------------------

class AnalysisReportCreateRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    summary: str = Field(..., min_length=10)
    findings: Optional[str] = None
    methodology: Optional[str] = None
    conclusion: Optional[str] = None
    evidence_ids: Optional[List[UUID]] = None


class AnalysisReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    case_id: UUID
    submitted_by: UUID
    title: str
    summary: str
    findings: Optional[str] = None
    methodology: Optional[str] = None
    conclusion: Optional[str] = None
    evidence_ids: Optional[str] = None
    report_file_name: Optional[str] = None
    sha256_hash: Optional[str] = None
    blockchain_tx_hash: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    analyst: Optional[UserResponse] = None


class AnalysisReportListResponse(BaseModel):
    items: List[AnalysisReportResponse]
    total: int
