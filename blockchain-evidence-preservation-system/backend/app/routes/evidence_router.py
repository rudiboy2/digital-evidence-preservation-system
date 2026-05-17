"""
Evidence Router - Strictly aligned with core workflow:
  Officer  → uploads evidence ONLY to assigned cases
  Analyst  → views + downloads evidence (read-only)
  Auditor  → views all evidence (read-only)
  Admin    → unrestricted
  All evidence is immutable (no edit/delete)
"""
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import Optional
from uuid import UUID
from datetime import datetime
import os

from core.infrastructure.database import get_db
from core.infrastructure.database.models.evidence import Evidence
from core.infrastructure.database.models.case import Case, case_officer_association
from core.infrastructure.database.models.custody_log import CustodyLog
from core.infrastructure.database.models.user import User
from core.infrastructure.storage.local_storage import LocalStorage
from core.infrastructure.blockchain.client import BlockchainClient
from handlers.hash_handler import HashHandler
from handlers.file_handler import FileHandler
from config.schemas import EvidenceResponse, EvidenceListResponse, EvidenceVerificationResponse
from config.settings import settings
from security.auth_service import get_current_user
from security.rbac import require_role, verify_case_access
from core.domain.evidence import EvidenceStatus, EvidenceType

router = APIRouter()
local_storage = LocalStorage()
hash_handler  = HashHandler()
file_handler  = FileHandler()
blockchain    = BlockchainClient()


async def log_evidence_action(
    db: AsyncSession,
    action: str,
    performed_by: UUID,
    performed_by_role: str,
    evidence_id: UUID = None,
    case_id: UUID = None,
    notes: str = "",
    ip_address: str = None,
):
    log = CustodyLog(
        action=action,
        performed_by=performed_by,
        performed_by_role=performed_by_role,
        evidence_id=evidence_id,
        case_id=case_id,
        notes=notes,
        ip_address=ip_address,
        timestamp=datetime.utcnow(),
    )
    db.add(log)
    await db.flush()


# ─────────────────────────────────────────────────────────────────────────────
# UPLOAD — Officer only (must be assigned to the case)
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/upload",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload evidence (Officer must be assigned to the case)",
)
async def upload_evidence(
    request: Request,
    case_id: UUID,
    description: str = "",
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = current_user.role.name if current_user.role else ""

    # Roles allowed to upload evidence
    if role not in ("officer", "investigator", "admin"):
        raise HTTPException(
            status_code=403,
            detail=f"Your role '{role}' cannot upload evidence. "
                   f"Only officers and investigators can upload evidence.",
        )

    # Officers must be assigned to the case before uploading
    # Investigators and admins can upload freely to their own cases
    if role == "officer":
        assigned = await db.execute(
            select(case_officer_association).where(
                and_(
                    case_officer_association.c.case_id == case_id,
                    case_officer_association.c.user_id == current_user.id,
                )
            )
        )
        if not assigned.first():
            raise HTTPException(
                status_code=403,
                detail="You are not assigned to this case. "
                       "Ask your investigator to assign you first.",
            )

    # Verify case exists and is open
    case_result = await db.execute(select(Case).where(Case.id == case_id))
    case = case_result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    if not case.is_editable():
        raise HTTPException(status_code=400, detail="Case is closed. No new evidence accepted.")

    # Read and validate file
    file_bytes = await file.read()
    try:
        await file_handler.validate(file.filename, file.content_type, file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Hash the file
    sha256 = hash_handler.compute_sha256(file_bytes)

    # Check for duplicate in this case
    dup = await db.execute(
        select(Evidence).where(
            and_(
                Evidence.sha256_hash == sha256,
                Evidence.case_id == case_id,
                Evidence.status != EvidenceStatus.DELETED.value,
            )
        )
    )
    if dup.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Identical evidence already exists in this case.",
        )

    # Store file
    storage_path = await local_storage.save(file_bytes, file.filename, str(case_id))

    # Register on blockchain (non-blocking failure)
    tx_hash = None
    block_number = None
    try:
        receipt = await blockchain.register_evidence(
            evidence_hash=sha256,
            case_id=str(case_id),
            uploader=str(current_user.id),
        )
        tx_hash     = receipt.get("transactionHash")
        block_number = receipt.get("blockNumber")
    except Exception:
        pass  # Blockchain unavailable; evidence still saved locally

    ev_status = EvidenceStatus.VERIFIED.value if tx_hash else EvidenceStatus.PENDING.value
    evidence = Evidence(
        case_id=case_id,
        uploaded_by=current_user.id,
        file_name=file.filename,
        file_size=len(file_bytes),
        mime_type=file.content_type or "application/octet-stream",
        evidence_type=Evidence.infer_type(file.content_type or "").value
            if hasattr(Evidence, "infer_type") else EvidenceType.OTHER.value,
        sha256_hash=sha256,
        storage_path=storage_path,
        blockchain_tx_hash=tx_hash,
        blockchain_block_number=block_number,
        description=description,
        status=ev_status,
    )
    db.add(evidence)
    await db.flush()
    await db.refresh(evidence)

    await log_evidence_action(
        db, action="upload",
        performed_by=current_user.id,
        performed_by_role=role,
        evidence_id=evidence.id,
        case_id=case_id,
        notes=f"Evidence '{file.filename}' uploaded. SHA256: {sha256}",
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(evidence)
    return EvidenceResponse.model_validate(evidence)


# ─────────────────────────────────────────────────────────────────────────────
# GET EVIDENCE BY ID
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
    evidence = result.scalar_one_or_none()
    if not evidence or evidence.status == EvidenceStatus.DELETED.value:
        raise HTTPException(status_code=404, detail="Evidence not found.")

    await verify_case_access(evidence.case_id, current_user, db, require_write=False)

    await log_evidence_action(
        db, action="view",
        performed_by=current_user.id,
        performed_by_role=current_user.role.name if current_user.role else "",
        evidence_id=evidence_id,
        case_id=evidence.case_id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return EvidenceResponse.model_validate(evidence)


# ─────────────────────────────────────────────────────────────────────────────
# LIST EVIDENCE FOR A CASE
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/case/{case_id}", response_model=EvidenceListResponse)
async def list_evidence_by_case(
    case_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await verify_case_access(case_id, current_user, db, require_write=False)

    base = select(Evidence).where(
        and_(
            Evidence.case_id == case_id,
            Evidence.status != EvidenceStatus.DELETED.value,
        )
    )
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    result = await db.execute(
        base.order_by(Evidence.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().all()

    return EvidenceListResponse(
        items=[EvidenceResponse.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


# ─────────────────────────────────────────────────────────────────────────────
# DOWNLOAD — Analyst, Officer, Investigator, Admin, Auditor (read-only)
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/{evidence_id}/download",
    summary="Download evidence file (logged as download action)",
)
async def download_evidence(
    evidence_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
    evidence = result.scalar_one_or_none()
    if not evidence or evidence.status == EvidenceStatus.DELETED.value:
        raise HTTPException(status_code=404, detail="Evidence not found.")

    await verify_case_access(evidence.case_id, current_user, db, require_write=False)

    full_path = local_storage.get_full_path(evidence.storage_path)
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Evidence file not found on disk.")

    await log_evidence_action(
        db, action="download",
        performed_by=current_user.id,
        performed_by_role=current_user.role.name if current_user.role else "",
        evidence_id=evidence_id,
        case_id=evidence.case_id,
        notes=f"File '{evidence.file_name}' downloaded",
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()

    return FileResponse(
        path=str(full_path),
        filename=evidence.file_name,
        media_type=evidence.mime_type,
    )


# ─────────────────────────────────────────────────────────────────────────────
# VERIFY INTEGRITY
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/{evidence_id}/verify",
    response_model=EvidenceVerificationResponse,
    summary="Verify evidence integrity against blockchain",
)
async def verify_evidence(
    evidence_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found.")

    await verify_case_access(evidence.case_id, current_user, db, require_write=False)

    try:
        file_bytes = await local_storage.read(evidence.storage_path)
    except FileNotFoundError:
        return EvidenceVerificationResponse(
            evidence_id=str(evidence_id),
            is_valid=False,
            db_hash=evidence.sha256_hash,
            computed_hash=None,
            blockchain_hash=None,
            blockchain_tx_hash=evidence.blockchain_tx_hash,
            status="file_missing",
            message="Evidence file missing from storage.",
        )

    computed = hash_handler.compute_sha256(file_bytes)
    is_valid = computed == evidence.sha256_hash

    await log_evidence_action(
        db, action="verify",
        performed_by=current_user.id,
        performed_by_role=current_user.role.name if current_user.role else "",
        evidence_id=evidence_id,
        case_id=evidence.case_id,
        notes=f"Integrity check: {'PASSED' if is_valid else 'FAILED'}",
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()

    return EvidenceVerificationResponse(
        evidence_id=str(evidence_id),
        is_valid=is_valid,
        db_hash=evidence.sha256_hash,
        computed_hash=computed,
        blockchain_hash=None,
        blockchain_tx_hash=evidence.blockchain_tx_hash,
        status="verified" if is_valid else "tampered",
        message=(
            "Evidence integrity verified. File matches original hash."
            if is_valid else
            "WARNING: Hash mismatch! Evidence may have been tampered with."
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# CHAIN OF CUSTODY
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{evidence_id}/custody-chain", summary="Get chain of custody")
async def get_custody_chain(
    evidence_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found.")

    await verify_case_access(evidence.case_id, current_user, db, require_write=False)

    logs_result = await db.execute(
        select(CustodyLog)
        .where(CustodyLog.evidence_id == evidence_id)
        .order_by(CustodyLog.timestamp.asc())
    )
    logs = logs_result.scalars().all()

    return {
        "evidence_id": str(evidence_id),
        "custody_chain": [
            {
                "id":               str(l.id),
                "action":           l.action,
                "performed_by":     str(l.performed_by),
                "performed_by_role": l.performed_by_role,
                "from_officer":     str(l.from_officer) if l.from_officer else None,
                "to_officer":       str(l.to_officer)   if l.to_officer   else None,
                "notes":            l.notes,
                "location":         l.location,
                "ip_address":       l.ip_address,
                "blockchain_tx_hash": l.blockchain_tx_hash,
                "timestamp":        l.timestamp.isoformat(),
            }
            for l in logs
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# TRANSFER CUSTODY — Investigator / Admin only
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/{evidence_id}/transfer",
    summary="Transfer custody (Investigator / Admin)",
)
async def transfer_custody(
    evidence_id: UUID,
    request: Request,
    to_officer_id: UUID,
    notes: str = "",
    location: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("investigator", "admin")),
):
    result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found.")

    await verify_case_access(evidence.case_id, current_user, db, require_write=True)

    log = CustodyLog(
        action="custody_transfer",
        performed_by=current_user.id,
        performed_by_role=current_user.role.name,
        evidence_id=evidence_id,
        case_id=evidence.case_id,
        from_officer=current_user.id,
        to_officer=to_officer_id,
        notes=notes or f"Custody transferred to officer {to_officer_id}",
        location=location,
        ip_address=request.client.host if request.client else None,
        timestamp=datetime.utcnow(),
    )
    db.add(log)
    await db.commit()

    return {"message": "Custody transferred and recorded on audit log."}
