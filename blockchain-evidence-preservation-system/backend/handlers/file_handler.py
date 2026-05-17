"""
File Handler - Validates and extracts metadata from uploaded evidence files.
"""
import magic
import logging
from pathlib import Path
from config.settings import settings

logger = logging.getLogger(__name__)

# Allowed MIME types for evidence upload
ALLOWED_MIME_TYPES = {
    # Documents
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "text/csv",
    # Images
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/bmp",
    "image/webp",
    # Video
    "video/mp4",
    "video/avi",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
    # Audio
    "audio/mpeg",
    "audio/wav",
    "audio/aac",
    "audio/ogg",
    # Archives
    "application/zip",
    "application/x-tar",
    "application/gzip",
    # Raw / binary forensic images
    "application/octet-stream",
}

DANGEROUS_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".ps1", ".vbs", ".js", ".msi",
    ".dll", ".so", ".dylib", ".php", ".py", ".rb", ".pl",
}


class FileHandler:
    """Validates uploaded evidence files before storage."""

    async def validate(
        self, filename: str, declared_mime: str, file_bytes: bytes
    ) -> None:
        """
        Validate an uploaded file.
        Raises ValueError if validation fails.
        """
        # Check file size
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise ValueError(
                f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB} MB."
            )

        if len(file_bytes) == 0:
            raise ValueError("File is empty.")

        # Check extension
        ext = Path(filename).suffix.lower()
        if ext in DANGEROUS_EXTENSIONS:
            raise ValueError(
                f"File extension '{ext}' is not permitted for evidence uploads."
            )

        # Verify actual MIME type using libmagic (prevents MIME spoofing)
        try:
            actual_mime = magic.from_buffer(file_bytes, mime=True)
        except Exception:
            logger.warning(f"libmagic unavailable; skipping MIME verification for {filename}")
            actual_mime = declared_mime

        if actual_mime not in ALLOWED_MIME_TYPES:
            raise ValueError(
                f"File type '{actual_mime}' is not permitted for evidence uploads."
            )

        logger.info(
            f"File validated: name={filename}, size={len(file_bytes)} bytes, "
            f"declared_mime={declared_mime}, actual_mime={actual_mime}"
        )

    def get_extension(self, filename: str) -> str:
        return Path(filename).suffix.lower()
