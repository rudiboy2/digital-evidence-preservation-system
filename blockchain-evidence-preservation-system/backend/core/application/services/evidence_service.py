"""
Evidence Service - Application layer orchestrating evidence operations.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from uuid import UUID

from core.infrastructure.database.repositories.evidence_repository import EvidenceRepository
from core.infrastructure.database.models.custody_log import CustodyLog
from core.domain.evidence import EvidenceStatus
from config.schemas import EvidenceResponse, EvidenceListResponse
from sqlalchemy import select, func


class EvidenceService:
    """Orchestrates evidence-related business operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = EvidenceRepository(db)

    async def get_evidence_by_id(self, evidence_id: UUID) -> Optional[EvidenceResponse]:
        """Fetch evidence by its primary key."""
        evidence = await self.repository.get_by_id(evidence_id)
        if not evidence or evidence.status == EvidenceStatus.DELETED:
            return None
        return EvidenceResponse.model_validate(evidence)

    async def list_evidence_by_case(
        self,
        case_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> EvidenceListResponse:
        """Retrieve paginated evidence list for a case."""
        items, total = await self.repository.list_by_case(
            case_id=case_id,
            offset=(page - 1) * page_size,
            limit=page_size,
        )
        return EvidenceListResponse(
            items=[EvidenceResponse.model_validate(e) for e in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size,
        )

    async def soft_delete_evidence(self, evidence_id: UUID) -> bool:
        """Soft-delete evidence; blockchain record remains intact."""
        return await self.repository.soft_delete(evidence_id)

    async def get_custody_chain(
        self, evidence_id: UUID
    ) -> Optional[List[Dict[str, Any]]]:
        """Retrieve the full chain of custody for a given evidence item."""
        evidence = await self.repository.get_by_id(evidence_id)
        if not evidence:
            return None

        result = await self.db.execute(
            select(CustodyLog)
            .where(CustodyLog.evidence_id == evidence_id)
            .order_by(CustodyLog.timestamp.asc())
        )
        logs = result.scalars().all()

        return [
            {
                "id": str(log.id),
                "action": log.action,
                "performed_by": str(log.performed_by),
                "notes": log.notes,
                "location": log.location,
                "blockchain_tx_hash": log.blockchain_tx_hash,
                "timestamp": log.timestamp.isoformat(),
            }
            for log in logs
        ]

    async def get_statistics(self) -> Dict[str, Any]:
        """Returns aggregate evidence statistics for dashboards."""
        total = await self.db.scalar(
            select(func.count()).select_from(
                __import__(
                    "core.infrastructure.database.models.evidence",
                    fromlist=["Evidence"],
                ).Evidence
            )
        )
        return {"total_evidence": total}
