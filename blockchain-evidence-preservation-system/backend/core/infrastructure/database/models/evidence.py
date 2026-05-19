"""
Evidence ORM Model - Extended with Tanzania 2026 forensic compliance fields.
Includes device metadata, collection details, GPS, witness, seal number.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Text, BigInteger, Integer, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.infrastructure.database import Base
from core.domain.evidence import EvidenceStatus, EvidenceType


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # File info
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(20), default=EvidenceType.OTHER.value, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    ipfs_cid: Mapped[str] = mapped_column(String(100), nullable=True)
    blockchain_tx_hash: Mapped[str] = mapped_column(String(66), nullable=True, index=True)
    blockchain_block_number: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=EvidenceStatus.PENDING.value, nullable=False)

    # ── OFFICER UNIQUE FIELDS ──────────────────────────────────────────────
    # Evidence source type
    evidence_source_type: Mapped[str] = mapped_column(String(50), nullable=True)
    # phone | laptop | usb | cctv | sd_card | cloud | network | email |
    # bank_records | digital_file | other

    # Physical device metadata (TPF-SOP-DE-2021)
    device_type: Mapped[str] = mapped_column(String(100), nullable=True)
    device_make: Mapped[str] = mapped_column(String(100), nullable=True)
    device_model: Mapped[str] = mapped_column(String(100), nullable=True)
    device_serial_number: Mapped[str] = mapped_column(String(100), nullable=True)
    device_imei: Mapped[str] = mapped_column(String(20), nullable=True)

    # Collection metadata
    collection_method: Mapped[str] = mapped_column(String(100), nullable=True)
    # physical_seizure | network_capture | cctv_extraction | mobile_extraction |
    # cloud_download | voluntarily_submitted
    collection_location: Mapped[str] = mapped_column(String(500), nullable=True)
    collection_gps_lat: Mapped[float] = mapped_column(Float, nullable=True)
    collection_gps_lng: Mapped[float] = mapped_column(Float, nullable=True)
    collection_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Witness and seal (Tanzania Evidence Act)
    witness_name: Mapped[str] = mapped_column(String(255), nullable=True)
    witness_badge_number: Mapped[str] = mapped_column(String(50), nullable=True)
    physical_seal_number: Mapped[str] = mapped_column(String(100), nullable=True)
    evidence_bag_number: Mapped[str] = mapped_column(String(100), nullable=True)
    exhibit_tag_number: Mapped[str] = mapped_column(String(100), nullable=True)

    # Linked witness statement reference
    witness_statement_ref: Mapped[str] = mapped_column(String(100), nullable=True)

    # Forensic copy tracking (analyst creates work copy)
    forensic_copy_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    # Hash of the forensic work copy (different from original hash)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="evidence")
    uploader: Mapped["User"] = relationship(
        "User", back_populates="evidence_uploaded", foreign_keys=[uploaded_by]
    )
    custody_logs: Mapped[list["CustodyLog"]] = relationship(
        "CustodyLog", back_populates="evidence", cascade="all, delete-orphan"
    )

    @staticmethod
    def infer_type(mime_type: str):
        from core.domain.evidence import EvidenceType
        if mime_type.startswith("image/"): return EvidenceType.IMAGE
        if mime_type.startswith("video/"): return EvidenceType.VIDEO
        if mime_type.startswith("audio/"): return EvidenceType.AUDIO
        if "pdf" in mime_type or "document" in mime_type or mime_type.startswith("text/"): return EvidenceType.DOCUMENT
        return EvidenceType.BINARY

    def __repr__(self) -> str:
        return f"<Evidence id={self.id} file_name={self.file_name}>"
