// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./access_control.sol";

/**
 * @title EvidenceRegistry
 * @notice Immutable on-chain registry for digital evidence hashes.
 *         Once evidence is registered, its record cannot be altered.
 * @dev Deployed by law enforcement agencies to ensure tamper-proof evidence tracking.
 */
contract EvidenceRegistry is AccessControlled {
    // -----------------------------------------------------------------------
    // Data Structures
    // -----------------------------------------------------------------------

    struct EvidenceRecord {
        bytes32 hash;          // SHA-256 hash of the evidence file
        string  caseId;        // Unique case identifier (off-chain DB UUID)
        address uploader;      // Ethereum address of the uploading officer
        uint256 timestamp;     // Unix timestamp of registration
        string  ipfsCid;       // IPFS Content Identifier (optional)
        bool    exists;        // Guard flag for existence checks
    }

    // -----------------------------------------------------------------------
    // State
    // -----------------------------------------------------------------------

    /// @dev Maps evidence hash → EvidenceRecord
    mapping(bytes32 => EvidenceRecord) private _registry;

    /// @dev Ordered list of all registered hashes (for enumeration)
    bytes32[] private _evidenceHashes;

    // -----------------------------------------------------------------------
    // Events
    // -----------------------------------------------------------------------

    event EvidenceRegistered(
        bytes32 indexed evidenceHash,
        string  indexed caseId,
        address indexed uploader,
        uint256 timestamp,
        string  ipfsCid
    );

    // -----------------------------------------------------------------------
    // Errors
    // -----------------------------------------------------------------------

    error EvidenceAlreadyRegistered(bytes32 hash);
    error EvidenceNotFound(bytes32 hash);

    // -----------------------------------------------------------------------
    // Constructor
    // -----------------------------------------------------------------------

    constructor(address admin) AccessControlled(admin) {}

    // -----------------------------------------------------------------------
    // External Functions
    // -----------------------------------------------------------------------

    /**
     * @notice Register a new piece of evidence on the blockchain.
     * @param evidenceHash  SHA-256 hash of the evidence file (as bytes32).
     * @param caseId        Off-chain case UUID string.
     * @param uploader      Ethereum address of the uploading officer.
     * @param ipfsCid       IPFS CID (empty string if not used).
     */
    function registerEvidence(
        bytes32 evidenceHash,
        string  calldata caseId,
        address uploader,
        string  calldata ipfsCid
    ) external onlyRole(OFFICER_ROLE) {
        if (_registry[evidenceHash].exists) {
            revert EvidenceAlreadyRegistered(evidenceHash);
        }

        _registry[evidenceHash] = EvidenceRecord({
            hash:      evidenceHash,
            caseId:    caseId,
            uploader:  uploader,
            timestamp: block.timestamp,
            ipfsCid:   ipfsCid,
            exists:    true
        });

        _evidenceHashes.push(evidenceHash);

        emit EvidenceRegistered(evidenceHash, caseId, uploader, block.timestamp, ipfsCid);
    }

    /**
     * @notice Retrieve the on-chain record for a given evidence hash.
     * @param evidenceHash  The SHA-256 hash to look up.
     */
    function getEvidence(bytes32 evidenceHash)
        external
        view
        returns (
            bytes32 hash,
            string  memory caseId,
            address uploader,
            uint256 timestamp,
            string  memory ipfsCid
        )
    {
        EvidenceRecord storage record = _registry[evidenceHash];
        if (!record.exists) {
            revert EvidenceNotFound(evidenceHash);
        }
        return (record.hash, record.caseId, record.uploader, record.timestamp, record.ipfsCid);
    }

    /**
     * @notice Check whether a given hash has been registered.
     */
    function isRegistered(bytes32 evidenceHash) external view returns (bool) {
        return _registry[evidenceHash].exists;
    }

    /**
     * @notice Returns the total number of registered evidence items.
     */
    function totalEvidence() external view returns (uint256) {
        return _evidenceHashes.length;
    }

    /**
     * @notice Enumerate evidence hashes by index (for off-chain indexers).
     */
    function evidenceHashAtIndex(uint256 index) external view returns (bytes32) {
        require(index < _evidenceHashes.length, "Index out of bounds");
        return _evidenceHashes[index];
    }
}
