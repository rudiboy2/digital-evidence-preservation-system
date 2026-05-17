"""
Evidence Repository - Data access layer for evidence records.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import Optional, Tuple, List
from uuid import UUID
from datetime import datetime

from core.infrastructure.database.models.evidence import Evidence
from core.domain.evidence import EvidenceStatus


class EvidenceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> Evidence:
        evidence = Evidence(**kwargs)
        self.db.add(evidence)
        await self.db.flush()
        await self.db.refresh(evidence)
        return evidence

    async def get_by_id(self, evidence_id: UUID) -> Optional[Evidence]:
        result = await self.db.execute(
            select(Evidence)
            .where(Evidence.id == evidence_id)
            .options(selectinload(Evidence.uploader), selectinload(Evidence.custody_logs))
        )
        return result.scalar_one_or_none()

    async def list_by_case(
        self,
        case_id: UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Evidence], int]:
        base_query = select(Evidence).where(
            and_(
                Evidence.case_id == case_id,
                Evidence.status != EvidenceStatus.DELETED.value,
            )
        )
        total_result = await self.db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = total_result.scalar()

        result = await self.db.execute(
            base_query
            .options(selectinload(Evidence.uploader))
            .order_by(Evidence.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = result.scalars().all()
        return items, total

    async def find_by_hash_in_case(self, sha256_hash: str, case_id: UUID) -> Optional[Evidence]:
        result = await self.db.execute(
            select(Evidence).where(
                and_(
                    Evidence.sha256_hash == sha256_hash,
                    Evidence.case_id == case_id,
                    Evidence.status != EvidenceStatus.DELETED.value,
                )
            )
        )
        return result.scalar_one_or_none()

    async def soft_delete(self, evidence_id: UUID) -> bool:
        evidence = await self.get_by_id(evidence_id)
        if not evidence:
            return False
        evidence.status = EvidenceStatus.DELETED.value
        evidence.deleted_at = datetime.utcnow()
        await self.db.flush()
        return True
