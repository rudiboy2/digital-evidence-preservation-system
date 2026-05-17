"""
Hash Handler - Cryptographic hashing utilities for evidence integrity.
"""
import hashlib
import hmac
from typing import Optional


class HashHandler:
    """Provides hashing utilities used for evidence integrity checks."""

    def compute_sha256(self, data: bytes) -> str:
        """Compute the SHA-256 hash of a byte sequence. Returns a hex string."""
        return hashlib.sha256(data).hexdigest()

    def compute_sha512(self, data: bytes) -> str:
        """Compute the SHA-512 hash of a byte sequence. Returns a hex string."""
        return hashlib.sha512(data).hexdigest()

    def compute_md5(self, data: bytes) -> str:
        """Compute MD5 (for legacy compatibility only; not used for security). Returns hex."""
        return hashlib.md5(data).hexdigest()

    def verify_sha256(self, data: bytes, expected_hash: str) -> bool:
        """Verify that data matches an expected SHA-256 hash (constant-time)."""
        actual = self.compute_sha256(data)
        return hmac.compare_digest(actual, expected_hash.lower())

    def compute_hash_from_path(self, file_path: str) -> str:
        """Compute SHA-256 hash by streaming a file from disk (memory-efficient)."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def hex_to_bytes32(hex_hash: str) -> bytes:
        """Convert a 64-char hex string to 32 bytes for Solidity bytes32 arguments."""
        clean = hex_hash.lstrip("0x")
        return bytes.fromhex(clean.zfill(64))
