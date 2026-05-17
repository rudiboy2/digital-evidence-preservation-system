"""
Tests for blockchain client and hash verification logic.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from handlers.hash_handler import HashHandler


def test_sha256_hash_consistency():
    handler = HashHandler()
    data = b"critical evidence file contents"
    hash1 = handler.compute_sha256(data)
    hash2 = handler.compute_sha256(data)
    assert hash1 == hash2
    assert len(hash1) == 64  # 32 bytes = 64 hex chars


def test_sha256_hash_different_data():
    handler = HashHandler()
    hash1 = handler.compute_sha256(b"file1 contents")
    hash2 = handler.compute_sha256(b"file2 contents")
    assert hash1 != hash2


def test_verify_sha256_correct():
    handler = HashHandler()
    data = b"evidence bytes"
    expected = handler.compute_sha256(data)
    assert handler.verify_sha256(data, expected) is True


def test_verify_sha256_tampered():
    handler = HashHandler()
    data = b"original evidence"
    tampered = b"tampered evidence"
    original_hash = handler.compute_sha256(data)
    assert handler.verify_sha256(tampered, original_hash) is False


def test_hex_to_bytes32():
    handler = HashHandler()
    hex_str = "a" * 64
    result = handler.hex_to_bytes32(hex_str)
    assert isinstance(result, bytes)
    assert len(result) == 32


@pytest.mark.asyncio
async def test_blockchain_client_not_connected():
    """Verify BlockchainClient raises when the node is unreachable."""
    from core.infrastructure.blockchain.client import BlockchainClient
    with patch("core.infrastructure.blockchain.client.Web3") as mock_web3_cls:
        mock_w3 = MagicMock()
        mock_w3.is_connected.return_value = False
        mock_web3_cls.return_value = mock_w3
        mock_web3_cls.HTTPProvider.return_value = MagicMock()

        client = BlockchainClient()
        client._w3 = mock_w3

        with pytest.raises(ConnectionError):
            await client.register_evidence(
                evidence_hash="a" * 64,
                case_id="test-case",
                uploader="0x0000000000000000000000000000000000000001",
            )
