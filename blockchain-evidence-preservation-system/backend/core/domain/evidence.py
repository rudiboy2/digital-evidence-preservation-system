"""
Evidence Domain Entity - Core business logic for evidence management.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4


class EvidenceStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    TAMPERED = "tampered"
    DELETED = "deleted"


class EvidenceType(str, Enum):
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    BINARY = "binary"
    OTHER = "other"


@dataclass
class Evidence:
    """Core domain entity representing a piece of digital evidence."""

    id: UUID = field(default_factory=uuid4)
    case_id: UUID = field(default=None)
    uploaded_by: UUID = field(default=None)
    file_name: str = field(default="")
    file_size: int = field(default=0)  # bytes
    mime_type: str = field(default="application/octet-stream")
    evidence_type: EvidenceType = field(default=EvidenceType.OTHER)
    sha256_hash: str = field(default="")
    storage_path: str = field(default="")
    ipfs_cid: Optional[str] = field(default=None)
    blockchain_tx_hash: Optional[str] = field(default=None)
    blockchain_block_number: Optional[int] = field(default=None)
    description: str = field(default="")
    status: EvidenceStatus = field(default=EvidenceStatus.PENDING)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = field(default=None)

    def is_tampered(self, current_hash: str) -> bool:
        """Check if the evidence has been tampered with by comparing hashes."""
        return self.sha256_hash != current_hash

    def mark_verified(self):
        """Mark this evidence as blockchain-verified."""
        self.status = EvidenceStatus.VERIFIED
        self.updated_at = datetime.utcnow()

    def mark_tampered(self):
        """Flag this evidence as potentially tampered."""
        self.status = EvidenceStatus.TAMPERED
        self.updated_at = datetime.utcnow()

    def soft_delete(self):
        """Soft-delete the evidence record while preserving the blockchain entry."""
        self.status = EvidenceStatus.DELETED
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @property
    def is_on_blockchain(self) -> bool:
        """Returns True if this evidence has been committed to the blockchain."""
        return self.blockchain_tx_hash is not None

    @property
    def file_size_mb(self) -> float:
        """File size in megabytes."""
        return self.file_size / (1024 * 1024)

    @classmethod
    def infer_type(cls, mime_type: str) -> "EvidenceType":
        """Infer the evidence type from the MIME type."""
        mime_map = {
            "image/": EvidenceType.IMAGE,
            "video/": EvidenceType.VIDEO,
            "audio/": EvidenceType.AUDIO,
            "application/pdf": EvidenceType.DOCUMENT,
            "text/": EvidenceType.DOCUMENT,
            "application/msword": EvidenceType.DOCUMENT,
            "application/vnd.openxmlformats": EvidenceType.DOCUMENT,
        }
        for prefix, ev_type in mime_map.items():
            if mime_type.startswith(prefix):
                return ev_type
        return EvidenceType.BINARY
