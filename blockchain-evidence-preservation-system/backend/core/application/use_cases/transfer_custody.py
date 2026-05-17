"""
Transfer Custody Use Case - Transfers custody of evidence between officers.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from core.infrastructure.database.repositories.evidence_repository import EvidenceRepository
from core.infrastructure.database.repositories.user_repository import UserRepository
from core.application.services.custody_service import CustodyService
from core.domain.custody import CustodyAction
from config.schemas import CustodyTransferRequest, CustodyLogResponse


class TransferCustodyUseCase:
    """
    Transfers custody of an evidence item from one officer to another.
    Both the database and blockchain are updated atomically.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.evidence_repo = EvidenceRepository(db)
        self.user_repo = UserRepository(db)
        self.custody_service = CustodyService(db)

    async def execute(
        self,
        evidence_id: UUID,
        from_officer_id: UUID,
        to_officer_id: UUID,
        notes: str = "",
        location: str = "",
    ) -> CustodyLogResponse:
        """Execute the custody transfer workflow."""

        # Validate evidence exists
        evidence = await self.evidence_repo.get_by_id(evidence_id)
        if not evidence:
            raise ValueError(f"Evidence {evidence_id} not found.")

        # Validate both users exist
        from_officer = await self.user_repo.get_by_id(from_officer_id)
        if not from_officer:
            raise ValueError(f"Transferring officer {from_officer_id} not found.")

        to_officer = await self.user_repo.get_by_id(to_officer_id)
        if not to_officer:
            raise ValueError(f"Receiving officer {to_officer_id} not found.")

        # Perform the transfer
        log = await self.custody_service.transfer_custody(
            evidence_id=evidence_id,
            from_officer=from_officer_id,
            to_officer=to_officer_id,
            notes=notes,
            location=location,
        )

        return CustodyLogResponse.model_validate(log)
