"""
Case Router - open -> under_review -> closed lifecycle enforced.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional
from datetime import datetime

from core.infrastructure.database import get_db
from core.infrastructure.database.models.case import (
    Case, case_officer_association, case_analyst_association
)
from core.infrastructure.database.models.user import User
from core.infrastructure.database.models.evidence import Evidence
from core.infrastructure.database.models.custody_log import CustodyLog
from config.schemas import (
    CaseCreateRequest, CaseUpdateRequest, CaseResponse,
    CaseListResponse, CaseTransitionRequest
)
from security.auth_service import get_current_user
from security.rbac import require_role, verify_case_access
from core.domain.case import Case as CaseDomain, CaseStatus

router = APIRouter()

# Enforces the only legal forward transitions.
# No skipping steps, no backward movement.
ALLOWED_TRANSITIONS = {
    "open":         "under_review",
    "under_review": "closed",
}


def _next_status_or_400(current_status: str) -> str:
    """Return the next valid status or raise HTTP 400."""
    next_status = ALLOWED_TRANSITIONS.get(current_status)
    if not next_status:
        if current_status == "closed":
            raise HTTPException(
                status_code=400,
                detail="Case is already closed. No further transitions are possible."
            )
        raise HTTPException(
            status_code=400,
            detail=f"No valid transition from status '{current_status}'.",
        )
    return next_status


async def log_action(
    db: AsyncSession,
    action: str,
    performed_by: UUID,
    performed_by_role: str,
    case_id: UUID = None,
    evidence_id: UUID = None,
    notes: str = "",
    ip_address: str = None,
):
    log = CustodyLog(
        action=action,
        performed_by=performed_by,
        performed_by_role=performed_by_role,
        case_id=case_id,
        evidence_id=evidence_id,
        notes=notes,
        ip_address=ip_address,
        timestamp=datetime.utcnow(),
    )
    db.add(log)
    await db.flush()


async def _attach_evidence_count(db: AsyncSession, case_id: UUID) -> int:
    count = await db.scalar(
        select(func.count(Evidence.id)).where(
            and_(Evidence.case_id == case_id, Evidence.status != "deleted")
        )
    )
    return count or 0


def _build_response(case: Case, evidence_count: int) -> CaseResponse:
    obj = CaseResponse.model_validate(case)
    obj.evidence_count = evidence_count
    return obj


# ─────────────────────────────────────────────────────────────────────────────
# CREATE CASE
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    request: Request,
    case_data: CaseCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("investigator", "admin")),
):
    case = Case(
        case_number=CaseDomain.generate_case_number(),
        title=case_data.title,
        description=case_data.description,
        priority=case_data.priority,
        jurisdiction=case_data.jurisdiction,
        incident_date=case_data.incident_date,
        warrant_number=case_data.warrant_number,
        warrant_issuing_court=case_data.warrant_issuing_court,
        warrant_issue_date=case_data.warrant_issue_date,
        warrant_expiry_date=case_data.warrant_expiry_date,
        ob_number=case_data.ob_number,
        dpp_reference_number=case_data.dpp_reference_number,
        court_name=case_data.court_name,
        court_case_number=case_data.court_case_number,
        next_hearing_date=case_data.next_hearing_date,
        court_status=case_data.court_status,
        referring_agency=case_data.referring_agency,
        external_reference=case_data.external_reference,
        created_by=current_user.id,
    )
    db.add(case)
    await db.flush()
    await log_action(
        db, action="case_created",
        performed_by=current_user.id,
        performed_by_role=current_user.role.name,
        case_id=case.id,
        notes=f"Case '{case_data.title}' created",
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(case)
    return _build_response(case, 0)


# ─────────────────────────────────────────────────────────────────────────────
# LIST CASES — role-filtered, real evidence_count
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/", response_model=CaseListResponse)
async def list_cases(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = current_user.role.name if current_user.role else ""
    query = select(Case).options(
        selectinload(Case.assigned_officers),
        selectinload(Case.assigned_analysts),
    )

    if role in ("admin", "auditor"):
        pass
    elif role == "investigator":
        query = query.where(Case.created_by == current_user.id)
    elif role == "officer":
        query = query.where(
            Case.id.in_(
                select(case_officer_association.c.case_id).where(
                    case_officer_association.c.user_id == current_user.id
                )
            )
        )
    elif role == "analyst":
        query = query.where(
            Case.id.in_(
                select(case_analyst_association.c.case_id).where(
                    case_analyst_association.c.user_id == current_user.id
                )
            )
        )

    if status_filter:
        query = query.where(Case.status == status_filter)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Case.created_at.desc()).offset(offset).limit(page_size)
    )
    cases = result.scalars().all()

    # Bulk evidence count — single grouped query
    case_ids = [c.id for c in cases]
    evidence_counts: dict = {}
    if case_ids:
        rows = await db.execute(
            select(Evidence.case_id, func.count(Evidence.id))
            .where(and_(Evidence.case_id.in_(case_ids), Evidence.status != "deleted"))
            .group_by(Evidence.case_id)
        )
        evidence_counts = {row[0]: row[1] for row in rows.all()}

    items = [
        _build_response(c, evidence_counts.get(c.id, 0))
        for c in cases
    ]

    return CaseListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET CASE BY ID
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_case_access(case_id, current_user, db, require_write=False)
    result = await db.execute(
        select(Case).where(Case.id == case_id)
        .options(selectinload(Case.assigned_officers), selectinload(Case.assigned_analysts))
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    await log_action(
        db, action="case_viewed",
        performed_by=current_user.id,
        performed_by_role=current_user.role.name if current_user.role else "",
        case_id=case_id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return _build_response(case, await _attach_evidence_count(db, case_id))


# ─────────────────────────────────────────────────────────────────────────────
# UPDATE CASE
# ─────────────────────────────────────────────────────────────────────────────
@router.patch("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: UUID,
    update_data: CaseUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("investigator", "admin")),
):
    await verify_case_access(case_id, current_user, db, require_write=True)
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(case, key, value)
    case.updated_at = datetime.utcnow()

    await log_action(
        db, action="case_updated",
        performed_by=current_user.id,
        performed_by_role=current_user.role.name,
        case_id=case_id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(case)
    return _build_response(case, await _attach_evidence_count(db, case_id))


# ─────────────────────────────────────────────────────────────────────────────
# ADVANCE STATUS — open -> under_review -> closed (one step at a time)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/{case_id}/advance-status", response_model=CaseResponse)
async def advance_case_status(
    case_id: UUID,
    request: Request,
    transition_data: CaseTransitionRequest = CaseTransitionRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("investigator", "admin")),
):
    await verify_case_access(case_id, current_user, db, require_write=True)
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    next_status = _next_status_or_400(case.status)
    prev_status = case.status
    case.status     = next_status
    case.updated_at = datetime.utcnow()

    if next_status == "closed":
        case.closed_at = datetime.utcnow()
        case.closed_by = current_user.id

    await log_action(
        db,
        action=f"case_status_{next_status}",
        performed_by=current_user.id,
        performed_by_role=current_user.role.name,
        case_id=case_id,
        notes=transition_data.notes or f"Status changed: {prev_status} → {next_status}",
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(case)
    return _build_response(case, await _attach_evidence_count(db, case_id))


# ─────────────────────────────────────────────────────────────────────────────
# CLOSE CASE — must already be under_review (enforces the flow)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/{case_id}/close", response_model=CaseResponse)
async def close_case(
    case_id: UUID,
    request: Request,
    transition_data: CaseTransitionRequest = CaseTransitionRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("investigator", "admin")),
):
    await verify_case_access(case_id, current_user, db, require_write=True)
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    if case.status == "open":
        raise HTTPException(
            status_code=400,
            detail="Case must be moved to 'Under Review' before it can be closed. "
                   "Use the 'Move to Under Review' action first.",
        )
    if case.status == "closed":
        raise HTTPException(status_code=400, detail="Case is already closed.")

    case.status     = "closed"
    case.closed_at  = datetime.utcnow()
    case.closed_by  = current_user.id
    case.updated_at = datetime.utcnow()

    await log_action(
        db, action="case_closed",
        performed_by=current_user.id,
        performed_by_role=current_user.role.name,
        case_id=case_id,
        notes=transition_data.notes or "Case closed",
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(case)
    return _build_response(case, await _attach_evidence_count(db, case_id))


# ─────────────────────────────────────────────────────────────────────────────
# ASSIGN OFFICER
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/{case_id}/assign-officer/{user_id}")
async def assign_officer(
    case_id: UUID,
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("investigator", "admin")),
):
    await verify_case_access(case_id, current_user, db, require_write=True)

    user_result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.role))
    )
    officer = user_result.scalar_one_or_none()
    if not officer:
        raise HTTPException(status_code=404, detail="User not found.")
    if officer.role.name not in ("officer", "admin"):
        raise HTTPException(status_code=400,
            detail=f"User '{officer.full_name}' has role '{officer.role.name}'. Only officers can be assigned here.")

    existing = await db.execute(
        select(case_officer_association).where(
            and_(case_officer_association.c.case_id == case_id,
                 case_officer_association.c.user_id == user_id)
        )
    )
    if existing.first():
        raise HTTPException(status_code=409, detail="Officer already assigned to this case.")

    await db.execute(case_officer_association.insert().values(case_id=case_id, user_id=user_id))
    await log_action(db, action="officer_assigned",
        performed_by=current_user.id, performed_by_role=current_user.role.name,
        case_id=case_id, notes=f"Officer {officer.full_name} assigned",
        ip_address=request.client.host if request.client else None)
    await db.commit()
    return {"message": f"Officer '{officer.full_name}' assigned to case."}


# ─────────────────────────────────────────────────────────────────────────────
# ASSIGN ANALYST
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/{case_id}/assign-analyst/{user_id}")
async def assign_analyst(
    case_id: UUID,
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("investigator", "admin")),
):
    await verify_case_access(case_id, current_user, db, require_write=True)

    user_result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.role))
    )
    analyst = user_result.scalar_one_or_none()
    if not analyst:
        raise HTTPException(status_code=404, detail="User not found.")
    if analyst.role.name not in ("analyst", "admin"):
        raise HTTPException(status_code=400,
            detail=f"User '{analyst.full_name}' has role '{analyst.role.name}'. Only analysts can be assigned here.")

    existing = await db.execute(
        select(case_analyst_association).where(
            and_(case_analyst_association.c.case_id == case_id,
                 case_analyst_association.c.user_id == user_id)
        )
    )
    if existing.first():
        raise HTTPException(status_code=409, detail="Analyst already assigned to this case.")

    await db.execute(case_analyst_association.insert().values(case_id=case_id, user_id=user_id))
    await log_action(db, action="analyst_assigned",
        performed_by=current_user.id, performed_by_role=current_user.role.name,
        case_id=case_id, notes=f"Analyst {analyst.full_name} assigned for forensic analysis",
        ip_address=request.client.host if request.client else None)
    await db.commit()
    return {"message": f"Analyst '{analyst.full_name}' assigned to case."}


# ─────────────────────────────────────────────────────────────────────────────
# AUDIT LOG
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{case_id}/audit-log")
async def get_case_audit_log(
    case_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_case_access(case_id, current_user, db, require_write=False)
    total = await db.scalar(
        select(func.count(CustodyLog.id)).where(CustodyLog.case_id == case_id)
    )
    result = await db.execute(
        select(CustodyLog).where(CustodyLog.case_id == case_id)
        .order_by(CustodyLog.timestamp.asc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    logs = result.scalars().all()
    return {
        "case_id": str(case_id), "total": total, "page": page, "page_size": page_size,
        "logs": [
            {
                "id": str(l.id), "action": l.action,
                "performed_by": str(l.performed_by),
                "performed_by_role": l.performed_by_role,
                "evidence_id": str(l.evidence_id) if l.evidence_id else None,
                "notes": l.notes, "ip_address": l.ip_address,
                "blockchain_tx_hash": l.blockchain_tx_hash,
                "timestamp": l.timestamp.isoformat(),
            }
            for l in logs
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# ADMISSIBILITY CHECK
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{case_id}/admissibility-check")
async def admissibility_check(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_case_access(case_id, current_user, db, require_write=False)
    result = await db.execute(
        select(Case).where(Case.id == case_id).options(
            selectinload(Case.evidence), selectinload(Case.analysis_reports),
            selectinload(Case.assigned_officers), selectinload(Case.assigned_analysts),
        )
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    checks = []
    missing = []

    def chk(label, passed, required=True, detail=""):
        s = "pass" if passed else ("fail" if required else "warning")
        if not passed: missing.append(label)
        checks.append({"label": label, "status": s, "required": required, "detail": detail})

    chk("Warrant Number recorded", bool(case.warrant_number),
        detail=case.warrant_number or "MISSING — required by Criminal Procedure Act Cap 20")
    chk("Warrant Issuing Court recorded", bool(case.warrant_issuing_court),
        detail=case.warrant_issuing_court or "MISSING")
    chk("OB Number recorded", bool(case.ob_number),
        detail=case.ob_number or "MISSING — required by TPF Evidence Manual 2019")
    chk("DPP Reference Number", bool(case.dpp_reference_number), required=False,
        detail=case.dpp_reference_number or "Not yet forwarded to DPP")

    ev = case.evidence or []
    chk("At least one evidence item uploaded", len(ev) > 0, detail=f"{len(ev)} evidence items")
    chk("All evidence has witness records", all(e.witness_name for e in ev) if ev else False)
    chk("All evidence has collection location", all(e.collection_location for e in ev) if ev else False)
    chk("All evidence hash-verified", all(e.status == "verified" for e in ev) if ev else False,
        detail="SHA-256 verification required by Evidence Act CAP 6 Section 34A")

    reports = case.analysis_reports or []
    chk("At least one forensic report submitted", len(reports) > 0, detail=f"{len(reports)} reports")
    if reports:
        r = reports[-1]
        chk("Analyst certification number", bool(r.analyst_certification_number),
            detail=r.analyst_certification_number or "MISSING — TCRA certification required")
        chk("Forensic tool name and version", bool(r.forensic_tool_name and r.forensic_tool_version))
        chk("Lab reference number", bool(r.lab_reference_number), required=False)
        chk("Examination dates recorded", bool(r.examination_start_date and r.examination_end_date))
        chk("Independence statement signed", bool(r.independence_statement))
        chk("Work copy hash recorded", bool(r.work_copy_hash))
        chk("Analyst declaration included", bool(r.analyst_declaration))

    chk("Officers assigned", len(case.assigned_officers) > 0)
    chk("Analysts assigned", len(case.assigned_analysts) > 0)

    total = len(checks)
    passed = sum(1 for c in checks if c["status"] == "pass")
    score  = int((passed / total) * 100) if total > 0 else 0
    ready  = score >= 80 and not any(c["status"] == "fail" and c["required"] for c in checks)

    return {
        "case_id": str(case_id), "case_number": case.case_number,
        "case_title": case.title, "checks": checks,
        "compliance_score": score, "passed": passed, "total": total,
        "is_court_ready": ready,
        "missing_required_items": [c["label"] for c in checks if c["status"] == "fail" and c["required"]],
        "warnings": [c["label"] for c in checks if c["status"] == "warning"],
        "generated_at": datetime.utcnow().isoformat(),
        "generated_by": str(current_user.id),
        "generated_by_role": current_user.role.name if current_user.role else "",
    }


# ─────────────────────────────────────────────────────────────────────────────
# SUBMIT TO COURT
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/{case_id}/submit-to-court")
async def submit_evidence_to_court(
    case_id: UUID,
    request: Request,
    court_case_number: str = "",
    court_name: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("investigator", "admin")),
):
    await verify_case_access(case_id, current_user, db, require_write=True)
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    case.evidence_submitted_to_court = True
    case.evidence_submitted_date     = datetime.utcnow()
    case.court_status                = "before_court"
    if court_case_number: case.court_case_number = court_case_number
    if court_name:        case.court_name        = court_name

    await log_action(db, action="evidence_submitted_to_court",
        performed_by=current_user.id, performed_by_role=current_user.role.name,
        case_id=case_id,
        notes=f"Evidence submitted to {court_name or case.court_name}",
        ip_address=request.client.host if request.client else None)
    await db.commit()
    return {
        "message": "Evidence submission to court recorded.",
        "case_id": str(case_id),
        "court_case_number": case.court_case_number,
        "submitted_at": case.evidence_submitted_date.isoformat(),
    }
