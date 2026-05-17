"""
Custody Domain Entity - Tracks chain of custody for evidence.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class CustodyAction(str, Enum):
    COLLECTED = "collected"
    UPLOADED = "uploaded"
    TRANSFERRED = "transferred"
    ACCESSED = "accessed"
    VERIFIED = "verified"
    EXPORTED = "exported"
    RETURNED = "returned"


@dataclass
class CustodyEntry:
    """
    Represents a single entry in the chain of custody for a piece of evidence.
    Each action is immutably recorded on the blockchain.
    """

    id: UUID = field(default_factory=uuid4)
    evidence_id: UUID = field(default=None)
    action: CustodyAction = field(default=CustodyAction.ACCESSED)
    performed_by: UUID = field(default=None)
    performed_by_name: str = field(default="")
    from_officer: Optional[UUID] = field(default=None)
    to_officer: Optional[UUID] = field(default=None)
    notes: str = field(default="")
    location: str = field(default="")
    blockchain_tx_hash: Optional[str] = field(default=None)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def is_transfer(self) -> bool:
        """Returns True if this entry represents a custody transfer."""
        return self.action == CustodyAction.TRANSFERRED

    @property
    def is_on_blockchain(self) -> bool:
        """Returns True if this custody entry is recorded on the blockchain."""
        return self.blockchain_tx_hash is not None

    def to_audit_string(self) -> str:
        """Returns a human-readable audit log string."""
        ts = self.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        base = f"[{ts}] {self.action.value.upper()} by {self.performed_by_name}"
        if self.is_transfer and self.to_officer:
            base += f" → transferred to officer {self.to_officer}"
        if self.notes:
            base += f' | Note: "{self.notes}"'
        if self.blockchain_tx_hash:
            base += f" | TX: {self.blockchain_tx_hash}"
        return base
