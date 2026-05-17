// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title AccessControlled
 * @notice Lightweight role-based access control for the evidence preservation system.
 *         Roles: ADMIN, OFFICER, AUDITOR
 */
contract AccessControlled {
    // -----------------------------------------------------------------------
    // Role Constants
    // -----------------------------------------------------------------------

    bytes32 public constant ADMIN_ROLE   = keccak256("ADMIN");
    bytes32 public constant OFFICER_ROLE = keccak256("OFFICER");
    bytes32 public constant AUDITOR_ROLE = keccak256("AUDITOR");

    // -----------------------------------------------------------------------
    // State
    // -----------------------------------------------------------------------

    /// @dev role → account → hasRole
    mapping(bytes32 => mapping(address => bool)) private _roles;

    // -----------------------------------------------------------------------
    // Events
    // -----------------------------------------------------------------------

    event RoleGranted(bytes32 indexed role, address indexed account, address indexed sender);
    event RoleRevoked(bytes32 indexed role, address indexed account, address indexed sender);

    // -----------------------------------------------------------------------
    // Errors
    // -----------------------------------------------------------------------

    error Unauthorized(address caller, bytes32 requiredRole);
    error CannotRevokeOwnAdmin();

    // -----------------------------------------------------------------------
    // Constructor
    // -----------------------------------------------------------------------

    constructor(address admin) {
        _grantRole(ADMIN_ROLE, admin);
        _grantRole(OFFICER_ROLE, admin); // Admin can also act as officer
    }

    // -----------------------------------------------------------------------
    // Modifiers
    // -----------------------------------------------------------------------

    modifier onlyRole(bytes32 role) {
        if (!_roles[role][msg.sender] && !_roles[ADMIN_ROLE][msg.sender]) {
            revert Unauthorized(msg.sender, role);
        }
        _;
    }

    modifier onlyAdmin() {
        if (!_roles[ADMIN_ROLE][msg.sender]) {
            revert Unauthorized(msg.sender, ADMIN_ROLE);
        }
        _;
    }

    // -----------------------------------------------------------------------
    // External Functions
    // -----------------------------------------------------------------------

    function grantRole(bytes32 role, address account) external onlyAdmin {
        _grantRole(role, account);
    }

    function revokeRole(bytes32 role, address account) external onlyAdmin {
        if (role == ADMIN_ROLE && account == msg.sender) {
            revert CannotRevokeOwnAdmin();
        }
        _revokeRole(role, account);
    }

    function hasRole(bytes32 role, address account) external view returns (bool) {
        return _roles[role][account];
    }

    // -----------------------------------------------------------------------
    // Internal Helpers
    // -----------------------------------------------------------------------

    function _grantRole(bytes32 role, address account) internal {
        if (!_roles[role][account]) {
            _roles[role][account] = true;
            emit RoleGranted(role, account, msg.sender);
        }
    }

    function _revokeRole(bytes32 role, address account) internal {
        if (_roles[role][account]) {
            _roles[role][account] = false;
            emit RoleRevoked(role, account, msg.sender);
        }
    }
}
