"""
User Router - Role-aware user listing:
  Admin       → sees ALL users
  Investigator → sees only officers and analysts (for assignment)
  Others      → can only view their own profile
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID

from core.infrastructure.database import get_db
from core.infrastructure.database.models.user import User
from core.infrastructure.database.models.role import Role
from config.schemas import UserResponse, UserListResponse
from security.auth_service import get_current_user

router = APIRouter()


@router.get(
    "/",
    response_model=UserListResponse,
    summary="List users — Admin sees all, Investigator sees officers and analysts",
)
async def list_users(
    role_filter: str = Query(None, alias="role"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    caller_role = current_user.role.name if current_user.role else ""

    # Build base query
    query = select(User).options(selectinload(User.role)).order_by(User.full_name.asc())

    if caller_role == "admin":
        # Admin sees everyone — optionally filtered by role
        if role_filter:
            query = query.join(Role).where(Role.name == role_filter)

    elif caller_role == "investigator":
        # Investigators only see officers and analysts (for case assignment)
        query = query.join(Role).where(
            Role.name.in_(["officer", "analyst"])
        )
        # Allow further filtering within allowed roles
        if role_filter and role_filter in ("officer", "analyst"):
            query = query.where(Role.name == role_filter)

    else:
        # All other roles: return only themselves
        query = query.where(User.id == current_user.id)

    result = await db.execute(query)
    users = result.scalars().all()

    # Filter out inactive users
    active_users = [u for u in users if u.is_active]

    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in active_users],
        total=len(active_users),
    )


@router.get(
    "/officers",
    response_model=UserListResponse,
    summary="List all officers — for assignment dropdowns",
)
async def list_officers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Endpoint specifically for getting officers for case assignment."""
    caller_role = current_user.role.name if current_user.role else ""
    if caller_role not in ("admin", "investigator"):
        raise HTTPException(status_code=403, detail="Access denied.")

    result = await db.execute(
        select(User)
        .join(Role)
        .where(Role.name == "officer", User.is_active == True)
        .options(selectinload(User.role))
        .order_by(User.full_name.asc())
    )
    users = result.scalars().all()
    return UserListResponse(items=[UserResponse.model_validate(u) for u in users], total=len(users))


@router.get(
    "/analysts",
    response_model=UserListResponse,
    summary="List all analysts — for assignment dropdowns",
)
async def list_analysts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Endpoint specifically for getting analysts for case assignment."""
    caller_role = current_user.role.name if current_user.role else ""
    if caller_role not in ("admin", "investigator"):
        raise HTTPException(status_code=403, detail="Access denied.")

    result = await db.execute(
        select(User)
        .join(Role)
        .where(Role.name == "analyst", User.is_active == True)
        .options(selectinload(User.role))
        .order_by(User.full_name.asc())
    )
    users = result.scalars().all()
    return UserListResponse(items=[UserResponse.model_validate(u) for u in users], total=len(users))


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    caller_role = current_user.role.name if current_user.role else ""
    if caller_role not in ("admin", "investigator") and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only view your own profile.")

    result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.role))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return UserResponse.model_validate(user)
