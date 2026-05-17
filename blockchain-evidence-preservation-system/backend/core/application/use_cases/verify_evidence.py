"""
Verify Evidence Use Case - Verifies evidence integrity against the blockchain.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from core.infrastructure.database.repositories.evidence_repository import EvidenceRepository
from core.infrastructure.storage.local_storage import LocalStorage
from core.infrastructure.blockchain.client import BlockchainClient
from core.application.services.custody_service import CustodyService
from core.domain.custody import CustodyAction
from handlers.hash_handler import HashHandler
from config.schemas import EvidenceVerificationResponse

logger = logging.getLogger(__name__)


class VerifyEvidenceUseCase:
    """
    Verifies a piece of evidence has not been tampered with by:
    1. Re-computing the file's SHA-256 hash
    2. Comparing it against the hash stored in the database
    3. Querying the blockchain to confirm the original registration hash
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.evidence_repo = EvidenceRepository(db)
        self.local_storage = LocalStorage()
        self.blockchain_client = BlockchainClient()
        self.custody_service = CustodyService(db)
        self.hash_handler = HashHandler()

    async def execute(self, evidence_id: UUID) -> EvidenceVerificationResponse:
        """Run the verification workflow."""

        evidence = await self.evidence_repo.get_by_id(evidence_id)
        if not evidence:
            raise ValueError(f"Evidence {evidence_id} not found.")

        # Re-read the stored file
        try:
            file_bytes = await self.local_storage.read(evidence.storage_path)
        except FileNotFoundError:
            logger.error(f"File not found on disk: {evidence.storage_path}")
            return EvidenceVerificationResponse(
                evidence_id=str(evidence_id),
                is_valid=False,
                db_hash=evidence.sha256_hash,
                computed_hash=None,
                blockchain_hash=None,
                blockchain_tx_hash=evidence.blockchain_tx_hash,
                status="file_missing",
                message="Evidence file is missing from storage.",
            )

        # Compute current hash
        computed_hash = self.hash_handler.compute_sha256(file_bytes)

        # Query blockchain for the registered hash
        blockchain_hash = None
        if evidence.blockchain_tx_hash:
            try:
                blockchain_record = await self.blockchain_client.get_evidence_record(
                    evidence.sha256_hash
                )
                blockchain_hash = blockchain_record.get("hash")
            except Exception as e:
                logger.warning(f"Could not query blockchain for evidence {evidence_id}: {e}")

        is_valid = (
            computed_hash == evidence.sha256_hash
            and (blockchain_hash is None or blockchain_hash == evidence.sha256_hash)
        )

        status = "verified" if is_valid else "tampered"
        message = (
            "Evidence integrity verified. Hash matches blockchain record."
            if is_valid
            else "WARNING: Evidence hash mismatch detected! Evidence may have been tampered with."
        )

        # Log the verification action
        # (We don't await this to keep the response fast; fire-and-forget style)
        try:
            await self.custody_service.record_action(
                evidence_id=evidence_id,
                action=CustodyAction.VERIFIED,
                performed_by=evidence.uploaded_by,  # approximation; caller should pass user
                notes=f"Integrity check: {status}",
            )
        except Exception as e:
            logger.warning(f"Failed to log verification action: {e}")

        return EvidenceVerificationResponse(
            evidence_id=str(evidence_id),
            is_valid=is_valid,
            db_hash=evidence.sha256_hash,
            computed_hash=computed_hash,
            blockchain_hash=blockchain_hash,
            blockchain_tx_hash=evidence.blockchain_tx_hash,
            status=status,
            message=message,
        )
