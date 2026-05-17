"""
RBAC - Strict Role-Based Access Control matching the core workflow:

  Officer     → upload evidence ONLY to assigned cases
  Investigator → create cases, assign analysts/officers, transfer custody
  Analyst     → view assigned cases, download evidence, submit reports
  Auditor     → read-only access to ALL data
  Admin       → unrestricted access
"""
from fastapi import Depends, HTTPException, Request, status
from typing import List
from uuid import UUID

from security.auth_service import get_current_user
from core.infrastructure.database.models.user import User
from core.infrastructure.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession


def require_role(*roles: str):
    """Enforce that the current user has one of the specified roles."""
    async def role_checker(current_user: User = Depends(get_current_user)):
        user_role = current_user.role.name if current_user.role else None
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Required role(s): {', '.join(roles)}. "
                    f"Your role: {user_role}."
                ),
            )
        return current_user
    return role_checker


async def verify_case_access(
    case_id: UUID,
    current_user: User,
    db: AsyncSession,
    require_write: bool = False,
) -> bool:
    """
    Verify that the current user can access a specific case.

    Rules:
    - Admin:        always allowed
    - Auditor:      read-only, always allowed
    - Investigator: allowed if they created the case
    - Officer:      allowed only if assigned to the case
    - Analyst:      allowed only if assigned to the case (read-only)

    If require_write=True, analysts and auditors are denied.
    """
    from sqlalchemy import select, and_
    from core.infrastructure.database.models.case import (
        Case, case_officer_association, case_analyst_association
    )

    role = current_user.role.name if current_user.role else ""

    # Admin: unrestricted
    if role == "admin":
        return True

    # Auditor: read-only, can see everything
    if role == "auditor":
        if require_write:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Auditors have read-only access.",
            )
        return True

    # Fetch the case
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    # Investigator: must be the creator
    if role == "investigator":
        if case.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Investigators can only access cases they created.",
            )
        return True

    # Officer: must be assigned to the case
    if role == "officer":
        if require_write is False:
            # Officers can view if assigned
            pass
        officer_result = await db.execute(
            select(case_officer_association).where(
                and_(
                    case_officer_association.c.case_id == case_id,
                    case_officer_association.c.user_id == current_user.id,
                )
            )
        )
        if not officer_result.first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Officers can only access cases they are assigned to.",
            )
        return True

    # Analyst: must be assigned to the case (read-only for evidence)
    if role == "analyst":
        if require_write:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Analysts cannot modify original evidence.",
            )
        analyst_result = await db.execute(
            select(case_analyst_association).where(
                and_(
                    case_analyst_association.c.case_id == case_id,
                    case_analyst_association.c.user_id == current_user.id,
                )
            )
        )
        if not analyst_result.first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Analysts can only access cases they are assigned to.",
            )
        return True

    raise HTTPException(status_code=403, detail="Access denied.")


class Permission:
    """Named permission constants."""
    UPLOAD_EVIDENCE       = "upload_evidence"
    VIEW_EVIDENCE         = "view_evidence"
    DOWNLOAD_EVIDENCE     = "download_evidence"
    DELETE_EVIDENCE       = "delete_evidence"
    TRANSFER_CUSTODY      = "transfer_custody"
    CREATE_CASE           = "create_case"
    CLOSE_CASE            = "close_case"
    ASSIGN_OFFICER        = "assign_officer"
    ASSIGN_ANALYST        = "assign_analyst"
    SUBMIT_REPORT         = "submit_report"
    VIEW_REPORTS          = "view_reports"
    MANAGE_USERS          = "manage_users"
    VIEW_AUDIT_LOG        = "view_audit_log"
    VIEW_ALL_CASES        = "view_all_cases"


# Strict role → permission mapping matching the workflow
ROLE_PERMISSIONS: dict[str, List[str]] = {
    "admin": [
        Permission.UPLOAD_EVIDENCE,
        Permission.VIEW_EVIDENCE,
        Permission.DOWNLOAD_EVIDENCE,
        Permission.DELETE_EVIDENCE,
        Permission.TRANSFER_CUSTODY,
        Permission.CREATE_CASE,
        Permission.CLOSE_CASE,
        Permission.ASSIGN_OFFICER,
        Permission.ASSIGN_ANALYST,
        Permission.SUBMIT_REPORT,
        Permission.VIEW_REPORTS,
        Permission.MANAGE_USERS,
        Permission.VIEW_AUDIT_LOG,
        Permission.VIEW_ALL_CASES,
    ],
    "investigator": [
        Permission.VIEW_EVIDENCE,
        Permission.DOWNLOAD_EVIDENCE,
        Permission.TRANSFER_CUSTODY,
        Permission.CREATE_CASE,
        Permission.CLOSE_CASE,
        Permission.ASSIGN_OFFICER,
        Permission.ASSIGN_ANALYST,
        Permission.VIEW_REPORTS,
        Permission.VIEW_AUDIT_LOG,
    ],
    "officer": [
        Permission.UPLOAD_EVIDENCE,
        Permission.VIEW_EVIDENCE,
        Permission.DOWNLOAD_EVIDENCE,
    ],
    "analyst": [
        Permission.VIEW_EVIDENCE,
        Permission.DOWNLOAD_EVIDENCE,
        Permission.SUBMIT_REPORT,
        Permission.VIEW_REPORTS,
        Permission.VIEW_AUDIT_LOG,
    ],
    "auditor": [
        Permission.VIEW_EVIDENCE,
        Permission.DOWNLOAD_EVIDENCE,
        Permission.VIEW_REPORTS,
        Permission.VIEW_AUDIT_LOG,
        Permission.VIEW_ALL_CASES,
    ],
}


def has_permission(role_name: str, permission: str) -> bool:
    """Check whether a role has a given permission."""
    return permission in ROLE_PERMISSIONS.get(role_name, [])
