"""
Upload Evidence Use Case - Orchestrates the complete evidence upload workflow.
"""
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from core.infrastructure.database.repositories.evidence_repository import EvidenceRepository
from core.infrastructure.database.repositories.case_repository import CaseRepository
from core.infrastructure.storage.ipfs_storage import IPFSStorage
from core.infrastructure.storage.local_storage import LocalStorage
from core.infrastructure.blockchain.client import BlockchainClient
from core.application.services.custody_service import CustodyService
from core.domain.evidence import Evidence, EvidenceStatus
from core.domain.custody import CustodyAction
from handlers.hash_handler import HashHandler
from handlers.file_handler import FileHandler
from config.settings import settings
from config.schemas import EvidenceResponse

logger = logging.getLogger(__name__)


class UploadEvidenceUseCase:
    """
    Orchestrates uploading evidence:
    1. Validate the file
    2. Compute SHA-256 hash
    3. Store file locally or on IPFS
    4. Register on the blockchain (evidence registry smart contract)
    5. Persist metadata to the database
    6. Create initial custody log entry
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.evidence_repo = EvidenceRepository(db)
        self.case_repo = CaseRepository(db)
        self.local_storage = LocalStorage()
        self.ipfs_storage = IPFSStorage()
        self.blockchain_client = BlockchainClient()
        self.custody_service = CustodyService(db)
        self.hash_handler = HashHandler()
        self.file_handler = FileHandler()

    async def execute(
        self,
        case_id: UUID,
        uploaded_by: UUID,
        file: UploadFile,
        description: str,
    ) -> EvidenceResponse:
        """Run the upload evidence workflow."""

        # 1. Validate the case exists
        case = await self.case_repo.get_by_id(case_id)
        if not case:
            raise ValueError(f"Case {case_id} does not exist.")
        if not case.is_editable():
            raise ValueError(f"Case {case_id} is closed and does not accept new evidence.")

        # 2. Read and validate file
        file_bytes = await file.read()
        await self.file_handler.validate(file.filename, file.content_type, file_bytes)

        # 3. Compute SHA-256 hash
        sha256_hash = self.hash_handler.compute_sha256(file_bytes)

        # 4. Check for duplicate evidence in this case
        duplicate = await self.evidence_repo.find_by_hash_in_case(sha256_hash, case_id)
        if duplicate:
            raise ValueError(
                f"Identical evidence (hash: {sha256_hash}) already exists in this case."
            )

        # 5. Store the file
        storage_path = await self.local_storage.save(
            file_bytes=file_bytes,
            filename=file.filename,
            case_id=str(case_id),
        )

        ipfs_cid = None
        if settings.IPFS_ENABLED:
            try:
                ipfs_cid = await self.ipfs_storage.pin(file_bytes, file.filename)
                logger.info(f"File pinned to IPFS: {ipfs_cid}")
            except Exception as e:
                logger.warning(f"IPFS storage failed, falling back to local only: {e}")

        # 6. Register on blockchain
        tx_hash = None
        block_number = None
        try:
            tx_receipt = await self.blockchain_client.register_evidence(
                evidence_hash=sha256_hash,
                case_id=str(case_id),
                uploader=str(uploaded_by),
                ipfs_cid=ipfs_cid or "",
            )
            tx_hash = tx_receipt.get("transactionHash")
            block_number = tx_receipt.get("blockNumber")
            logger.info(f"Evidence registered on blockchain: tx={tx_hash}")
        except Exception as e:
            logger.error(f"Blockchain registration failed: {e}")
            # We continue; the evidence is stored locally and will be retried

        # 7. Persist to database
        from core.domain.evidence import EvidenceType
        evidence_orm = await self.evidence_repo.create(
            case_id=case_id,
            uploaded_by=uploaded_by,
            file_name=file.filename,
            file_size=len(file_bytes),
            mime_type=file.content_type or "application/octet-stream",
            evidence_type=Evidence.infer_type(file.content_type or "").value,
            sha256_hash=sha256_hash,
            storage_path=storage_path,
            ipfs_cid=ipfs_cid,
            blockchain_tx_hash=tx_hash,
            blockchain_block_number=block_number,
            description=description,
            status=EvidenceStatus.VERIFIED.value if tx_hash else EvidenceStatus.PENDING.value,
        )

        # 8. Create initial custody log
        await self.custody_service.record_action(
            evidence_id=evidence_orm.id,
            action=CustodyAction.UPLOADED,
            performed_by=uploaded_by,
            notes=f"Initial upload: {file.filename}",
        )

        logger.info(f"Evidence {evidence_orm.id} uploaded successfully.")
        return EvidenceResponse.model_validate(evidence_orm)
