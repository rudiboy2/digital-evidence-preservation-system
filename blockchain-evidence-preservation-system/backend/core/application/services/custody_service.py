"""
Custody Service - Manages chain-of-custody operations and blockchain recording.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime

from core.infrastructure.database.models.custody_log import CustodyLog
from core.infrastructure.blockchain.client import BlockchainClient
from core.domain.custody import CustodyAction


class CustodyService:
    """Handles creating and recording custody log entries."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.blockchain_client = BlockchainClient()

    async def record_action(
        self,
        evidence_id: UUID,
        action: CustodyAction,
        performed_by: UUID,
        notes: str = "",
        location: str = "",
        from_officer: UUID = None,
        to_officer: UUID = None,
    ) -> CustodyLog:
        """
        Record a custody action in both the database and on the blockchain.
        """
        # Record on blockchain first for immutability
        tx_hash = await self.blockchain_client.record_custody_event(
            evidence_id=str(evidence_id),
            action=action.value,
            officer_id=str(performed_by),
            timestamp=int(datetime.utcnow().timestamp()),
        )

        log = CustodyLog(
            evidence_id=evidence_id,
            action=action.value,
            performed_by=performed_by,
            from_officer=from_officer,
            to_officer=to_officer,
            notes=notes,
            location=location,
            blockchain_tx_hash=tx_hash,
            timestamp=datetime.utcnow(),
        )

        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def transfer_custody(
        self,
        evidence_id: UUID,
        from_officer: UUID,
        to_officer: UUID,
        notes: str = "",
        location: str = "",
    ) -> CustodyLog:
        """Transfer custody from one officer to another."""
        return await self.record_action(
            evidence_id=evidence_id,
            action=CustodyAction.TRANSFERRED,
            performed_by=from_officer,
            from_officer=from_officer,
            to_officer=to_officer,
            notes=notes,
            location=location,
        )
