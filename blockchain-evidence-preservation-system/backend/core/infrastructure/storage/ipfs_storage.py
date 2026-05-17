"""
IPFS Storage - Pins evidence files to IPFS for decentralised storage.
"""
import aiohttp
import logging
from typing import Optional

from config.settings import settings

logger = logging.getLogger(__name__)


class IPFSStorage:
    """
    Handles pinning files to IPFS via the Kubo (go-ipfs) HTTP API.
    Falls back gracefully if IPFS is not available.
    """

    def __init__(self):
        self.api_url = settings.IPFS_API_URL  # e.g. "http://localhost:5001"

    async def pin(self, file_bytes: bytes, filename: str) -> Optional[str]:
        """
        Pin a file to IPFS. Returns the CID (Content Identifier) or None on failure.
        """
        form = aiohttp.FormData()
        form.add_field(
            "file",
            file_bytes,
            filename=filename,
            content_type="application/octet-stream",
        )

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/api/v0/add?pin=true&quieter=true",
                data=form,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                cid = data.get("Hash")
                logger.info(f"File pinned to IPFS: cid={cid}")
                return cid

    async def retrieve(self, cid: str) -> bytes:
        """
        Retrieve a file from IPFS by its CID.
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/api/v0/cat?arg={cid}",
                timeout=aiohttp.ClientTimeout(total=300),
            ) as resp:
                resp.raise_for_status()
                return await resp.read()

    async def unpin(self, cid: str) -> bool:
        """
        Remove a pin from IPFS (the data remains until garbage-collected).
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/api/v0/pin/rm?arg={cid}",
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 200:
                    logger.info(f"IPFS pin removed: cid={cid}")
                    return True
                return False

    def get_gateway_url(self, cid: str) -> str:
        """Return a public IPFS gateway URL for a given CID."""
        return f"https://ipfs.io/ipfs/{cid}"
