"""
Pydantic Schemas - Tanzania 2026 legally compliant request/response models.
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
# Case — Investigator Features (Tanzania Legal Compliance)
# ---------------------------------------------------------------------------
class CaseCreateRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    description: Optional[str] = None
    priority: str = Field(default="medium")
    jurisdiction: Optional[str] = None
    incident_date: Optional[datetime] = None
    # Legal authority fields
    warrant_number: Optional[str] = None
    warrant_issuing_court: Optional[str] = None
    warrant_issue_date: Optional[datetime] = None
    warrant_expiry_date: Optional[datetime] = None
    ob_number: Optional[str] = None
    dpp_reference_number: Optional[str] = None
    # Court tracking
    court_name: Optional[str] = None
    court_case_number: Optional[str] = None
    next_hearing_date: Optional[datetime] = None
    court_status: Optional[str] = None
    # Inter-agency
    referring_agency: Optional[str] = None
    external_reference: Optional[str] = None


class CaseUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=500)
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    jurisdiction: Optional[str] = None
    warrant_number: Optional[str] = None
    warrant_issuing_court: Optional[str] = None
    warrant_issue_date: Optional[datetime] = None
    warrant_expiry_date: Optional[datetime] = None
    ob_number: Optional[str] = None
    dpp_reference_number: Optional[str] = None
    court_name: Optional[str] = None
    court_case_number: Optional[str] = None
    next_hearing_date: Optional[datetime] = None
    court_status: Optional[str] = None
    referring_agency: Optional[str] = None
    external_reference: Optional[str] = None

class CaseAssignRequest(BaseModel):
    user_id: UUID
    role: Optional[str] = "officer"
    notes: Optional[str] = None


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
    # Legal fields
    warrant_number: Optional[str] = None
    warrant_issuing_court: Optional[str] = None
    warrant_issue_date: Optional[datetime] = None
    warrant_expiry_date: Optional[datetime] = None
    ob_number: Optional[str] = None
    dpp_reference_number: Optional[str] = None
    court_name: Optional[str] = None
    court_case_number: Optional[str] = None
    next_hearing_date: Optional[datetime] = None
    court_status: Optional[str] = None
    referring_agency: Optional[str] = None
    external_reference: Optional[str] = None
    evidence_submitted_to_court: Optional[bool] = None
    evidence_submitted_date: Optional[datetime] = None
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
# Evidence — Officer Features (Tanzania Forensic Compliance)
# ---------------------------------------------------------------------------
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
    # Officer collection fields
    evidence_source_type: Optional[str] = None
    device_type: Optional[str] = None
    device_make: Optional[str] = None
    device_model: Optional[str] = None
    device_serial_number: Optional[str] = None
    device_imei: Optional[str] = None
    collection_method: Optional[str] = None
    collection_location: Optional[str] = None
    collection_gps_lat: Optional[float] = None
    collection_gps_lng: Optional[float] = None
    collection_date: Optional[datetime] = None
    witness_name: Optional[str] = None
    witness_badge_number: Optional[str] = None
    physical_seal_number: Optional[str] = None
    evidence_bag_number: Optional[str] = None
    exhibit_tag_number: Optional[str] = None
    witness_statement_ref: Optional[str] = None
    forensic_copy_hash: Optional[str] = None
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
# Analysis Report — Analyst Features (TDFL-STD-2023)
# ---------------------------------------------------------------------------
class AnalysisReportCreateRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    summary: str = Field(..., min_length=10)
    findings: Optional[str] = None
    methodology: Optional[str] = None
    conclusion: Optional[str] = None
    evidence_ids: Optional[List[UUID]] = None
    # TDFL mandatory fields
    analyst_certification_number: Optional[str] = None
    forensic_tool_name: Optional[str] = None
    forensic_tool_version: Optional[str] = None
    lab_reference_number: Optional[str] = None
    examination_start_date: Optional[datetime] = None
    examination_end_date: Optional[datetime] = None
    work_copy_hash: Optional[str] = None
    independence_statement: Optional[bool] = False
    independence_statement_text: Optional[str] = None
    copies_made: Optional[int] = None
    copies_location: Optional[str] = None
    is_expert_witness: Optional[bool] = False
    expert_witness_court_designation: Optional[str] = None
    analyst_declaration: Optional[str] = None


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
    analyst_certification_number: Optional[str] = None
    forensic_tool_name: Optional[str] = None
    forensic_tool_version: Optional[str] = None
    lab_reference_number: Optional[str] = None
    examination_start_date: Optional[datetime] = None
    examination_end_date: Optional[datetime] = None
    work_copy_hash: Optional[str] = None
    independence_statement: Optional[bool] = None
    independence_statement_text: Optional[str] = None
    copies_made: Optional[int] = None
    copies_location: Optional[str] = None
    is_expert_witness: Optional[bool] = None
    expert_witness_court_designation: Optional[str] = None
    analyst_declaration: Optional[str] = None
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


# ---------------------------------------------------------------------------
# Admissibility Checklist — Auditor Feature
# ---------------------------------------------------------------------------
class AdmissibilityChecklistResponse(BaseModel):
    case_id: str
    case_number: str
    checks: List[dict]
    compliance_score: int
    is_court_ready: bool
    missing_items: List[str]
    generated_at: str
