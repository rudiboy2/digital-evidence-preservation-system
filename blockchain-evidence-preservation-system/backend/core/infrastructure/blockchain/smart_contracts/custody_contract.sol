// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./access_control.sol";

/**
 * @title CustodyContract
 * @notice Records immutable chain-of-custody events for digital evidence.
 *         Every transfer, access, and verification action is permanently logged.
 */
contract CustodyContract is AccessControlled {
    // -----------------------------------------------------------------------
    // Data Structures
    // -----------------------------------------------------------------------

    struct CustodyEvent {
        bytes32 evidenceHash;   // Reference to the evidence item
        string  action;         // e.g. "uploaded", "transferred", "verified"
        address officer;        // Officer who performed the action
        address fromOfficer;    // For transfers: previous custodian
        address toOfficer;      // For transfers: new custodian
        uint256 timestamp;      // On-chain block timestamp
        string  notes;          // Optional notes
    }

    // -----------------------------------------------------------------------
    // State
    // -----------------------------------------------------------------------

    /// @dev Maps evidence hash → ordered list of custody events
    mapping(bytes32 => CustodyEvent[]) private _custodyChain;

    // -----------------------------------------------------------------------
    // Events
    // -----------------------------------------------------------------------

    event CustodyEventRecorded(
        bytes32 indexed evidenceHash,
        string  action,
        address indexed officer,
        uint256 timestamp
    );

    event CustodyTransferred(
        bytes32 indexed evidenceHash,
        address indexed fromOfficer,
        address indexed toOfficer,
        uint256 timestamp
    );

    // -----------------------------------------------------------------------
    // Constructor
    // -----------------------------------------------------------------------

    constructor(address admin) AccessControlled(admin) {}

    // -----------------------------------------------------------------------
    // External Functions
    // -----------------------------------------------------------------------

    /**
     * @notice Record a general custody action.
     */
    function recordCustodyEvent(
        bytes32        evidenceHash,
        string calldata action,
        address        officer,
        uint256        timestamp
    ) external onlyRole(OFFICER_ROLE) {
        _custodyChain[evidenceHash].push(CustodyEvent({
            evidenceHash: evidenceHash,
            action:       action,
            officer:      officer,
            fromOfficer:  address(0),
            toOfficer:    address(0),
            timestamp:    timestamp == 0 ? block.timestamp : timestamp,
            notes:        ""
        }));

        emit CustodyEventRecorded(evidenceHash, action, officer, block.timestamp);
    }

    /**
     * @notice Record a custody transfer between two officers.
     */
    function transferCustody(
        bytes32 evidenceHash,
        address fromOfficer,
        address toOfficer,
        string  calldata notes
    ) external onlyRole(OFFICER_ROLE) {
        _custodyChain[evidenceHash].push(CustodyEvent({
            evidenceHash: evidenceHash,
            action:       "transferred",
            officer:      msg.sender,
            fromOfficer:  fromOfficer,
            toOfficer:    toOfficer,
            timestamp:    block.timestamp,
            notes:        notes
        }));

        emit CustodyTransferred(evidenceHash, fromOfficer, toOfficer, block.timestamp);
    }

    /**
     * @notice Get a specific custody event by index.
     */
    function getCustodyEvent(bytes32 evidenceHash, uint256 index)
        external
        view
        returns (
            string  memory action,
            address officer,
            address fromOfficer,
            address toOfficer,
            uint256 timestamp,
            string  memory notes
        )
    {
        require(index < _custodyChain[evidenceHash].length, "Index out of bounds");
        CustodyEvent storage ev = _custodyChain[evidenceHash][index];
        return (ev.action, ev.officer, ev.fromOfficer, ev.toOfficer, ev.timestamp, ev.notes);
    }

    /**
     * @notice Returns the total number of custody events for an evidence item.
     */
    function getCustodyChainLength(bytes32 evidenceHash) external view returns (uint256) {
        return _custodyChain[evidenceHash].length;
    }
}
