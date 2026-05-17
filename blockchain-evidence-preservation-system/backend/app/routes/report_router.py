"""
Report Router - Analyst submits forensic analysis reports.
Only analysts (assigned to case) and admin can submit reports.
All roles with case access can view reports.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime
from typing import Optional

from core.infrastructure.database import get_db
from core.infrastructure.database.models.analysis_report import AnalysisReport
from core.infrastructure.database.models.custody_log import CustodyLog
from core.infrastructure.database.models.case import case_analyst_association
from core.infrastructure.database.models.user import User
from core.infrastructure.storage.local_storage import LocalStorage
from handlers.hash_handler import HashHandler
from config.schemas import (
    AnalysisReportCreateRequest, AnalysisReportResponse, AnalysisReportListResponse
)
from security.auth_service import get_current_user
from security.rbac import require_role, verify_case_access

router = APIRouter()
local_storage = LocalStorage()
hash_handler  = HashHandler()


# ─────────────────────────────────────────────────────────────────────────────
# SUBMIT REPORT — Analyst (assigned to case) and Admin
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/cases/{case_id}/reports",
    response_model=AnalysisReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit forensic analysis report (Analyst only)",
)
async def submit_report(
    case_id: UUID,
    request: Request,
    report_data: AnalysisReportCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = current_user.role.name if current_user.role else ""

    if role not in ("analyst", "admin"):
        raise HTTPException(
            status_code=403,
            detail=f"Only analysts can submit reports. Your role: '{role}'.",
        )

    # Analyst must be assigned to this case
    if role == "analyst":
        assigned = await db.execute(
            select(case_analyst_association).where(
                and_(
                    case_analyst_association.c.case_id == case_id,
                    case_analyst_association.c.user_id == current_user.id,
                )
            )
        )
        if not assigned.first():
            raise HTTPException(
                status_code=403,
                detail="You are not assigned to this case.",
            )

    evidence_ids_str = (
        ",".join(str(eid) for eid in report_data.evidence_ids)
        if report_data.evidence_ids else None
    )

    report = AnalysisReport(
        case_id=case_id,
        submitted_by=current_user.id,
        title=report_data.title,
        summary=report_data.summary,
        findings=report_data.findings,
        methodology=report_data.methodology,
        conclusion=report_data.conclusion,
        evidence_ids=evidence_ids_str,
        status="submitted",
        submitted_at=datetime.utcnow(),
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)

    # Audit log
    log = CustodyLog(
        action="report_submission",
        performed_by=current_user.id,
        performed_by_role=role,
        case_id=case_id,
        notes=f"Forensic report '{report_data.title}' submitted",
        ip_address=request.client.host if request.client else None,
        timestamp=datetime.utcnow(),
    )
    db.add(log)
    await db.commit()
    await db.refresh(report)
    return AnalysisReportResponse.model_validate(report)


# ─────────────────────────────────────────────────────────────────────────────
# LIST REPORTS FOR A CASE
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/cases/{case_id}/reports",
    response_model=AnalysisReportListResponse,
    summary="List all reports for a case",
)
async def list_reports(
    case_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_case_access(case_id, current_user, db, require_write=False)

    total = await db.scalar(
        select(func.count(AnalysisReport.id)).where(AnalysisReport.case_id == case_id)
    )
    result = await db.execute(
        select(AnalysisReport)
        .where(AnalysisReport.case_id == case_id)
        .options(selectinload(AnalysisReport.analyst))
        .order_by(AnalysisReport.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().all()

    return AnalysisReportListResponse(
        items=[AnalysisReportResponse.model_validate(r) for r in items],
        total=total,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET SINGLE REPORT
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/reports/{report_id}",
    response_model=AnalysisReportResponse,
    summary="Get a single analysis report",
)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AnalysisReport)
        .where(AnalysisReport.id == report_id)
        .options(selectinload(AnalysisReport.analyst))
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    await verify_case_access(report.case_id, current_user, db, require_write=False)
    return AnalysisReportResponse.model_validate(report)
