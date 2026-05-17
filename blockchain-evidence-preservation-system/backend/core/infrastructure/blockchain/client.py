"""
Blockchain Client - Interfaces with Ethereum smart contracts via Web3.py.
"""
import logging
from typing import Optional, Dict, Any
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account

from config.settings import settings

logger = logging.getLogger(__name__)

# Minimal ABI for the EvidenceRegistry smart contract
EVIDENCE_REGISTRY_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "evidenceHash", "type": "bytes32"},
            {"internalType": "string", "name": "caseId", "type": "string"},
            {"internalType": "address", "name": "uploader", "type": "address"},
            {"internalType": "string", "name": "ipfsCid", "type": "string"},
        ],
        "name": "registerEvidence",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "evidenceHash", "type": "bytes32"}],
        "name": "getEvidence",
        "outputs": [
            {"internalType": "bytes32", "name": "hash", "type": "bytes32"},
            {"internalType": "string", "name": "caseId", "type": "string"},
            {"internalType": "address", "name": "uploader", "type": "address"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "string", "name": "ipfsCid", "type": "string"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

CUSTODY_CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "evidenceHash", "type": "bytes32"},
            {"internalType": "string", "name": "action", "type": "string"},
            {"internalType": "address", "name": "officer", "type": "address"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
        ],
        "name": "recordCustodyEvent",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


class BlockchainClient:
    """Async-compatible client for interacting with Ethereum smart contracts."""

    def __init__(self):
        self._w3: Optional[Web3] = None
        self._account: Optional[Account] = None

    @property
    def w3(self) -> Web3:
        if self._w3 is None:
            self._w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC_URL))
            self._w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            if not self._w3.is_connected():
                logger.warning("Could not connect to blockchain node at %s", settings.BLOCKCHAIN_RPC_URL)
        return self._w3

    @property
    def account(self):
        if self._account is None and settings.BLOCKCHAIN_PRIVATE_KEY:
            self._account = Account.from_key(settings.BLOCKCHAIN_PRIVATE_KEY)
        return self._account

    def _get_evidence_registry(self):
        return self.w3.eth.contract(
            address=Web3.to_checksum_address(settings.EVIDENCE_REGISTRY_CONTRACT_ADDRESS),
            abi=EVIDENCE_REGISTRY_ABI,
        )

    def _get_custody_contract(self):
        return self.w3.eth.contract(
            address=Web3.to_checksum_address(settings.CUSTODY_CONTRACT_ADDRESS),
            abi=CUSTODY_CONTRACT_ABI,
        )

    async def register_evidence(
        self,
        evidence_hash: str,
        case_id: str,
        uploader: str,
        ipfs_cid: str = "",
    ) -> Dict[str, Any]:
        """Register evidence on the blockchain. Returns transaction receipt."""
        if not self.w3.is_connected():
            raise ConnectionError("Not connected to blockchain node.")

        contract = self._get_evidence_registry()
        hash_bytes = Web3.to_bytes(hexstr=evidence_hash) if evidence_hash.startswith("0x") \
            else bytes.fromhex(evidence_hash)

        tx = contract.functions.registerEvidence(
            hash_bytes,
            case_id,
            Web3.to_checksum_address(uploader) if Web3.is_address(uploader) else self.account.address,
            ipfs_cid,
        ).build_transaction({
            "from": self.account.address,
            "nonce": self.w3.eth.get_transaction_count(self.account.address),
            "gas": 200000,
            "gasPrice": self.w3.eth.gas_price,
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx, settings.BLOCKCHAIN_PRIVATE_KEY)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        return {
            "transactionHash": receipt.transactionHash.hex(),
            "blockNumber": receipt.blockNumber,
            "status": receipt.status,
        }

    async def get_evidence_record(self, evidence_hash: str) -> Dict[str, Any]:
        """Query the blockchain for an evidence record."""
        if not self.w3.is_connected():
            raise ConnectionError("Not connected to blockchain node.")

        contract = self._get_evidence_registry()
        hash_bytes = bytes.fromhex(evidence_hash.lstrip("0x"))
        result = contract.functions.getEvidence(hash_bytes).call()

        return {
            "hash": result[0].hex(),
            "case_id": result[1],
            "uploader": result[2],
            "timestamp": result[3],
            "ipfs_cid": result[4],
        }

    async def record_custody_event(
        self,
        evidence_id: str,
        action: str,
        officer_id: str,
        timestamp: int,
    ) -> Optional[str]:
        """Record a custody action on the blockchain. Returns tx hash or None."""
        if not self.w3.is_connected():
            logger.warning("Blockchain not connected; skipping custody event recording.")
            return None

        contract = self._get_custody_contract()
        hash_bytes = bytes.fromhex(evidence_id.replace("-", "").ljust(64, "0")[:64])

        tx = contract.functions.recordCustodyEvent(
            hash_bytes,
            action,
            self.account.address,
            timestamp,
        ).build_transaction({
            "from": self.account.address,
            "nonce": self.w3.eth.get_transaction_count(self.account.address),
            "gas": 150000,
            "gasPrice": self.w3.eth.gas_price,
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx, settings.BLOCKCHAIN_PRIVATE_KEY)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        return receipt.transactionHash.hex()
