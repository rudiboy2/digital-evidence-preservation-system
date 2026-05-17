"""
Local Storage - Saves and retrieves evidence files from the local filesystem.
"""
import os
import aiofiles
import logging
from pathlib import Path
from typing import Optional

from config.settings import settings

logger = logging.getLogger(__name__)


class LocalStorage:
    """Handles secure local filesystem storage for evidence files."""

    def __init__(self):
        self.base_path = Path(settings.EVIDENCE_STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, file_bytes: bytes, filename: str, case_id: str) -> str:
        """
        Save file bytes to a case-scoped directory.
        Returns the relative storage path.
        """
        # Sanitize filename
        safe_filename = Path(filename).name.replace(" ", "_")
        case_dir = self.base_path / case_id
        case_dir.mkdir(parents=True, exist_ok=True)

        file_path = case_dir / safe_filename

        # If file already exists with same name, append a counter
        counter = 1
        while file_path.exists():
            stem = Path(safe_filename).stem
            suffix = Path(safe_filename).suffix
            file_path = case_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_bytes)

        relative_path = str(file_path.relative_to(settings.EVIDENCE_STORAGE_PATH))
        logger.info(f"Evidence saved to: {relative_path}")
        return relative_path

    async def read(self, storage_path: str) -> bytes:
        """
        Read and return the bytes of a stored evidence file.
        Raises FileNotFoundError if the file does not exist.
        """
        full_path = self.base_path / storage_path
        if not full_path.exists():
            raise FileNotFoundError(f"Evidence file not found: {full_path}")

        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, storage_path: str) -> bool:
        """
        Delete a file from local storage.
        Returns True if deleted, False if not found.
        """
        full_path = self.base_path / storage_path
        if full_path.exists():
            full_path.unlink()
            logger.info(f"Evidence file deleted: {storage_path}")
            return True
        return False

    def get_full_path(self, storage_path: str) -> Path:
        return self.base_path / storage_path
