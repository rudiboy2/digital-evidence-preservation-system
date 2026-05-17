"""
Case Repository - Data access layer for case records.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, Tuple, List
from uuid import UUID
from datetime import datetime

from core.infrastructure.database.models.case import Case
from core.domain.case import CaseStatus, Case as CaseDomain
from config.schemas import CaseCreateRequest, CaseUpdateRequest, CaseListResponse, CaseResponse


class CaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: CaseCreateRequest, created_by: UUID) -> Case:
        case_number = CaseDomain.generate_case_number()
        case = Case(
            case_number=case_number,
            title=data.title,
            description=data.description,
            priority=data.priority,
            jurisdiction=data.jurisdiction,
            incident_date=data.incident_date,
            created_by=created_by,
        )
        self.db.add(case)
        await self.db.flush()
        await self.db.refresh(case)
        return case

    async def get_by_id(self, case_id: UUID) -> Optional[Case]:
        result = await self.db.execute(
            select(Case)
            .where(Case.id == case_id)
            .options(
                selectinload(Case.creator),
                selectinload(Case.assigned_officers),
                selectinload(Case.evidence),
            )
        )
        return result.scalar_one_or_none()

    async def list_cases(
        self,
        page: int,
        page_size: int,
        status_filter: Optional[str],
        user_id: UUID,
        user_role: str,
    ) -> CaseListResponse:
        query = select(Case)
        if user_role not in ("admin", "auditor"):
            # Non-admins only see cases they created or are assigned to
            query = query.where(
                or_(
                    Case.created_by == user_id,
                    Case.assigned_officers.any(id=user_id),
                )
            )
        if status_filter:
            query = query.where(Case.status == status_filter)

        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        offset = (page - 1) * page_size
        result = await self.db.execute(
            query
            .options(selectinload(Case.creator))
            .order_by(Case.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = result.scalars().all()
        return CaseListResponse(
            items=[CaseResponse.model_validate(c) for c in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size,
        )

    async def update(self, case_id: UUID, data: CaseUpdateRequest) -> Optional[Case]:
        case = await self.get_by_id(case_id)
        if not case:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(case, key, value)
        case.updated_at = datetime.utcnow()
        await self.db.flush()
        return case

    async def close_case(self, case_id: UUID, closed_by: UUID) -> Optional[Case]:
        case = await self.get_by_id(case_id)
        if not case:
            return None
        case.status = CaseStatus.CLOSED.value
        case.closed_at = datetime.utcnow()
        case.closed_by = closed_by
        await self.db.flush()
        return case

    async def assign_user(self, case_id: UUID, user_id: UUID) -> bool:
        from core.infrastructure.database.models.user import User
        case = await self.get_by_id(case_id)
        if not case:
            return False
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return False
        case.assigned_officers.append(user)
        await self.db.flush()
        return True
