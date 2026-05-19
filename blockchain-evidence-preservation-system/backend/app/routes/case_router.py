"""
Case Router - Strictly aligned with core workflow:
  - Investigator creates and manages cases
  - Investigator assigns officers and analysts
  - Auditor/Admin view all cases
  - Officer/Analyst see only assigned cases
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional
from datetime import datetime

from core.infrastructure.database import get_db
from core.infrastructure.database.models.case import (
    Case, case_officer_association, case_analyst_association
)
from core.infrastructure.database.models.user import User
from core.infrastructure.database.models.custody_log import CustodyLog
from config.schemas import (
    CaseCreateRequest, CaseUpdateRequest, CaseResponse,
    CaseListResponse, CaseAssignRequest
)
from security.auth_service import get_current_user
from security.rbac import require_role, verify_case_access, has_permission
from core.domain.case import Case as CaseDomain, CaseStatus

router = APIRouter()


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
    """Record every action to the audit trail."""
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


# ─────────────────────────────────────────────────────────────────────────────
# CREATE CASE — Investigator and Admin only
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new case (Investigator / Admin only)",
)
async def create_case(
    request: Request,
    case_data: CaseCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("investigator", "admin")),
):
    case_number = CaseDomain.generate_case_number()
    case = Case(
        case_number=case_number,
        title=case_data.title,
        description=case_data.description,
        priority=case_data.priority,
        jurisdiction=case_data.jurisdiction,
        incident_date=case_data.incident_date,
        created_by=current_user.id,
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)

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
    return case


# ─────────────────────────────────────────────────────────────────────────────
# LIST CASES — Role-filtered
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/", response_model=CaseListResponse, summary="List cases (role-filtered)")
async def list_cases(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = current_user.role.name if current_user.role else ""
    query = select(Case).options(
        selectinload(Case.assigned_officers),
        selectinload(Case.assigned_analysts),
    )

    # Apply role-based filtering
    if role in ("admin", "auditor"):
        # See all cases
        pass
    elif role == "investigator":
        # Only cases they created
        query = query.where(Case.created_by == current_user.id)
    elif role == "officer":
        # Only cases they are assigned to
        query = query.where(
            Case.id.in_(
                select(case_officer_association.c.case_id).where(
                    case_officer_association.c.user_id == current_user.id
                )
            )
        )
    elif role == "analyst":
        # Only cases they are assigned to
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
    items = result.scalars().all()

    return CaseListResponse(
        items=[CaseResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET CASE BY ID — Access verified per role
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{case_id}", response_model=CaseResponse, summary="Get case by ID")
async def get_case(
    case_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_case_access(case_id, current_user, db, require_write=False)

    result = await db.execute(
        select(Case)
        .where(Case.id == case_id)
        .options(
            selectinload(Case.assigned_officers),
            selectinload(Case.assigned_analysts),
        )
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    # Log view action
    await log_action(
        db, action="case_viewed",
        performed_by=current_user.id,
        performed_by_role=current_user.role.name if current_user.role else "",
        case_id=case_id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return CaseResponse.model_validate(case)


# ─────────────────────────────────────────────────────────────────────────────
# UPDATE CASE — Investigator (own cases) and Admin
# ─────────────────────────────────────────────────────────────────────────────
@router.patch(
    "/{case_id}",
    response_model=CaseResponse,
    summary="Update case (Investigator / Admin)",
)
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
    return CaseResponse.model_validate(case)


# ─────────────────────────────────────────────────────────────────────────────
# CLOSE CASE — Investigator (own) and Admin
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/{case_id}/close",
    response_model=CaseResponse,
    summary="Close a case",
)
async def close_case(
    case_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("investigator", "admin")),
):
    await verify_case_access(case_id, current_user, db, require_write=True)

    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    case.status   = CaseStatus.CLOSED.value
    case.closed_at = datetime.utcnow()
    case.closed_by = current_user.id

    await log_action(
        db, action="case_closed",
        performed_by=current_user.id,
        performed_by_role=current_user.role.name,
        case_id=case_id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(case)
    return CaseResponse.model_validate(case)


# ─────────────────────────────────────────────────────────────────────────────
# ASSIGN OFFICER — Investigator assigns officers to upload evidence
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/{case_id}/assign-officer/{user_id}",
    summary="Assign an officer to a case (Investigator / Admin)",
)
async def assign_officer(
    case_id: UUID,
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("investigator", "admin")),
):
    await verify_case_access(case_id, current_user, db, require_write=True)

    # Verify the user being assigned has the officer role
    user_result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.role))
    )
    officer = user_result.scalar_one_or_none()
    if not officer:
        raise HTTPException(status_code=404, detail="User not found.")
    if officer.role.name not in ("officer", "admin"):
        raise HTTPException(
            status_code=400,
            detail=f"User '{officer.full_name}' has role '{officer.role.name}'. Only officers can be assigned here.",
        )

    # Check not already assigned
    existing = await db.execute(
        select(case_officer_association).where(
            and_(
                case_officer_association.c.case_id == case_id,
                case_officer_association.c.user_id == user_id,
            )
        )
    )
    if existing.first():
        raise HTTPException(status_code=409, detail="Officer already assigned to this case.")

    await db.execute(
        case_officer_association.insert().values(case_id=case_id, user_id=user_id)
    )
    await log_action(
        db, action="officer_assigned",
        performed_by=current_user.id,
        performed_by_role=current_user.role.name,
        case_id=case_id,
        notes=f"Officer {officer.full_name} assigned",
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"message": f"Officer '{officer.full_name}' assigned to case."}


# ─────────────────────────────────────────────────────────────────────────────
# ASSIGN ANALYST — Investigator assigns analysts for forensic analysis
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/{case_id}/assign-analyst/{user_id}",
    summary="Assign an analyst to a case (Investigator / Admin)",
)
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
        raise HTTPException(
            status_code=400,
            detail=f"User '{analyst.full_name}' has role '{analyst.role.name}'. Only analysts can be assigned here.",
        )

    existing = await db.execute(
        select(case_analyst_association).where(
            and_(
                case_analyst_association.c.case_id == case_id,
                case_analyst_association.c.user_id == user_id,
            )
        )
    )
    if existing.first():
        raise HTTPException(status_code=409, detail="Analyst already assigned to this case.")

    await db.execute(
        case_analyst_association.insert().values(case_id=case_id, user_id=user_id)
    )
    await log_action(
        db, action="analyst_assigned",
        performed_by=current_user.id,
        performed_by_role=current_user.role.name,
        case_id=case_id,
        notes=f"Analyst {analyst.full_name} assigned for forensic analysis",
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"message": f"Analyst '{analyst.full_name}' assigned to case."}


# ─────────────────────────────────────────────────────────────────────────────
# GET AUDIT LOG FOR A CASE
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/{case_id}/audit-log",
    summary="Get full audit log for a case",
)
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
        select(CustodyLog)
        .where(CustodyLog.case_id == case_id)
        .order_by(CustodyLog.timestamp.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    logs = result.scalars().all()

    return {
        "case_id": str(case_id),
        "total": total,
        "page": page,
        "page_size": page_size,
        "logs": [
            {
                "id":               str(log.id),
                "action":           log.action,
                "performed_by":     str(log.performed_by),
                "performed_by_role": log.performed_by_role,
                "evidence_id":      str(log.evidence_id) if log.evidence_id else None,
                "notes":            log.notes,
                "ip_address":       log.ip_address,
                "blockchain_tx_hash": log.blockchain_tx_hash,
                "timestamp":        log.timestamp.isoformat(),
            }
            for log in logs
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# ADMISSIBILITY CHECKLIST — Auditor & Admin
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/{case_id}/admissibility-check",
    summary="Generate court admissibility checklist (Auditor / Admin)",
)
async def admissibility_check(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generates a compliance checklist based on Tanzania court requirements.
    Checks all mandatory fields for digital evidence admissibility.
    """
    await verify_case_access(case_id, current_user, db, require_write=False)

    result = await db.execute(
        select(Case)
        .where(Case.id == case_id)
        .options(
            selectinload(Case.evidence),
            selectinload(Case.analysis_reports),
            selectinload(Case.assigned_officers),
            selectinload(Case.assigned_analysts),
        )
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    checks = []
    missing = []

    def chk(label, passed, required=True, detail=""):
        status = "pass" if passed else ("fail" if required else "warning")
        if not passed:
            missing.append(label)
        checks.append({
            "label": label,
            "status": status,
            "required": required,
            "detail": detail,
        })

    # Legal authority checks
    chk("Warrant Number recorded",
        bool(case.warrant_number),
        detail=case.warrant_number or "MISSING — required by Criminal Procedure Act Cap 20")
    chk("Warrant Issuing Court recorded",
        bool(case.warrant_issuing_court),
        detail=case.warrant_issuing_court or "MISSING")
    chk("OB Number recorded",
        bool(case.ob_number),
        detail=case.ob_number or "MISSING — required by TPF Evidence Manual 2019")
    chk("DPP Reference Number",
        bool(case.dpp_reference_number), required=False,
        detail=case.dpp_reference_number or "Not yet forwarded to DPP")

    # Evidence checks
    evidence_list = case.evidence or []
    chk("At least one evidence item uploaded",
        len(evidence_list) > 0,
        detail=f"{len(evidence_list)} evidence items")

    all_have_seal = all(e.physical_seal_number for e in evidence_list) if evidence_list else False
    chk("All evidence has physical seal numbers",
        all_have_seal or not evidence_list, required=False,
        detail="Required for physical device evidence")

    all_have_bag = all(e.evidence_bag_number for e in evidence_list) if evidence_list else False
    chk("All evidence has bag/exhibit numbers",
        all_have_bag or not evidence_list, required=False,
        detail="Required by TPF Evidence Manual 2019")

    all_have_witness = all(e.witness_name for e in evidence_list) if evidence_list else False
    chk("All evidence has witness records",
        all_have_witness or not evidence_list,
        detail="Witness required at point of collection")

    all_have_location = all(e.collection_location for e in evidence_list) if evidence_list else False
    chk("All evidence has collection location",
        all_have_location or not evidence_list,
        detail="Collection location required for court")

    all_verified = all(
        e.status in ("verified",) for e in evidence_list
    ) if evidence_list else False
    chk("All evidence hash-verified against blockchain",
        all_verified or not evidence_list,
        detail="SHA-256 verification required by Evidence Act CAP 6 Section 34A")

    # Analyst report checks
    reports = case.analysis_reports or []
    chk("At least one forensic analysis report submitted",
        len(reports) > 0,
        detail=f"{len(reports)} reports")

    if reports:
        latest = reports[-1]
        chk("Analyst certification number in report",
            bool(latest.analyst_certification_number),
            detail=latest.analyst_certification_number or "MISSING — TCRA certification required")
        chk("Forensic tool name and version recorded",
            bool(latest.forensic_tool_name and latest.forensic_tool_version),
            detail=f"{latest.forensic_tool_name} {latest.forensic_tool_version}" if latest.forensic_tool_name else "MISSING — required by TDFL-STD-2023")
        chk("Lab reference number recorded",
            bool(latest.lab_reference_number), required=False,
            detail=latest.lab_reference_number or "Recommended for TDFL submissions")
        chk("Examination dates recorded",
            bool(latest.examination_start_date and latest.examination_end_date),
            detail="Required by TDFL-STD-2023")
        chk("Independence statement signed",
            bool(latest.independence_statement),
            detail="Required for court testimony")
        chk("Work copy hash recorded",
            bool(latest.work_copy_hash),
            detail="Original must never be examined directly")
        chk("Analyst declaration included",
            bool(latest.analyst_declaration),
            detail="Required for court-admissible reports")

    # Team assignment checks
    chk("Officers assigned to case",
        len(case.assigned_officers) > 0,
        detail=f"{len(case.assigned_officers)} officer(s) assigned")
    chk("Analysts assigned to case",
        len(case.assigned_analysts) > 0,
        detail=f"{len(case.assigned_analysts)} analyst(s) assigned")

    total = len(checks)
    passed = sum(1 for c in checks if c["status"] == "pass")
    score = int((passed / total) * 100) if total > 0 else 0
    is_court_ready = score >= 80 and not any(
        c["status"] == "fail" and c["required"] for c in checks
    )

    return {
        "case_id": str(case_id),
        "case_number": case.case_number,
        "case_title": case.title,
        "checks": checks,
        "compliance_score": score,
        "passed": passed,
        "total": total,
        "is_court_ready": is_court_ready,
        "missing_required_items": [c["label"] for c in checks if c["status"] == "fail" and c["required"]],
        "warnings": [c["label"] for c in checks if c["status"] == "warning"],
        "generated_at": datetime.utcnow().isoformat(),
        "generated_by": str(current_user.id),
        "generated_by_role": current_user.role.name if current_user.role else "",
    }


# ─────────────────────────────────────────────────────────────────────────────
# SUBMIT EVIDENCE TO COURT — Investigator / Admin
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/{case_id}/submit-to-court",
    summary="Mark evidence as submitted to court (Investigator / Admin)",
)
async def submit_evidence_to_court(
    case_id: UUID,
    request: Request,
    court_case_number: str = "",
    court_name: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("investigator", "admin")),
):
    """
    Marks the case evidence as formally submitted to court.
    Creates an immutable blockchain-logged audit entry.
    """
    await verify_case_access(case_id, current_user, db, require_write=True)

    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    case.evidence_submitted_to_court = True
    case.evidence_submitted_date = datetime.utcnow()
    case.court_status = "before_court"
    if court_case_number:
        case.court_case_number = court_case_number
    if court_name:
        case.court_name = court_name

    await log_action(
        db, action="evidence_submitted_to_court",
        performed_by=current_user.id,
        performed_by_role=current_user.role.name,
        case_id=case_id,
        notes=f"Evidence formally submitted to {court_name or case.court_name}. Court case: {court_case_number or case.court_case_number}",
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()

    return {
        "message": "Evidence submission to court recorded.",
        "case_id": str(case_id),
        "court_case_number": case.court_case_number,
        "submitted_at": case.evidence_submitted_date.isoformat(),
    }
