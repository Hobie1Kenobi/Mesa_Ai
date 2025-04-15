// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

/**
 * @title RightsVault
 * @dev Smart contract for privacy-preserving music rights management
 */
contract RightsVault {
    // Structs
    struct EncryptedRight {
        bytes encryptedData;     // Encrypted rights data (ECIES)
        bytes32 dataHash;        // Hash of unencrypted data for verification
        uint256 timestamp;       // When this right was registered/updated
        bool verified;           // Whether this right has been verified
        address verifier;        // Address that verified this right
    }
    
    struct AccessPermission {
        bool hasAccess;          // Whether this viewer has access
        uint256 expiresAt;       // When access expires (0 for no expiration)
        uint256 lastAccessed;    // When access was last used
    }
    
    // State variables
    mapping(address => mapping(bytes32 => EncryptedRight)) private userRights;
    mapping(address => mapping(address => mapping(bytes32 => AccessPermission))) private accessPermissions;
    mapping(address => bytes32[]) private userRightsList;
    
    // Events
    event RightRegistered(address indexed owner, bytes32 indexed rightId);
    event RightUpdated(address indexed owner, bytes32 indexed rightId);
    event RightVerified(address indexed owner, bytes32 indexed rightId, address indexed verifier);
    event AccessGranted(address indexed owner, address indexed viewer, bytes32 indexed rightId, uint256 expiresAt);
    event AccessRevoked(address indexed owner, address indexed viewer, bytes32 indexed rightId);
    event RightAccessed(address indexed owner, address indexed viewer, bytes32 indexed rightId);
    
    /**
     * @dev Register a new encrypted right
     * @param rightId Unique identifier for the right
     * @param encryptedData Encrypted rights data
     * @param dataHash Hash of the unencrypted data
     */
    function registerRight(bytes32 rightId, bytes calldata encryptedData, bytes32 dataHash) external {
        require(userRights[msg.sender][rightId].timestamp == 0, "Right already exists");
        
        userRights[msg.sender][rightId] = EncryptedRight({
            encryptedData: encryptedData,
            dataHash: dataHash,
            timestamp: block.timestamp,
            verified: false,
            verifier: address(0)
        });
        
        userRightsList[msg.sender].push(rightId);
        
        emit RightRegistered(msg.sender, rightId);
    }
    
    /**
     * @dev Update an existing right
     * @param rightId Unique identifier for the right
     * @param encryptedData New encrypted rights data
     * @param dataHash New hash of the unencrypted data
     */
    function updateRight(bytes32 rightId, bytes calldata encryptedData, bytes32 dataHash) external {
        require(userRights[msg.sender][rightId].timestamp > 0, "Right does not exist");
        
        userRights[msg.sender][rightId].encryptedData = encryptedData;
        userRights[msg.sender][rightId].dataHash = dataHash;
        userRights[msg.sender][rightId].timestamp = block.timestamp;
        
        emit RightUpdated(msg.sender, rightId);
    }
    
    /**
     * @dev Verify a right (can only be called by authorized verifiers)
     * @param owner Address of the rights owner
     * @param rightId Unique identifier for the right
     */
    function verifyRight(address owner, bytes32 rightId) external {
        require(userRights[owner][rightId].timestamp > 0, "Right does not exist");
        
        // In a production version, we would check if msg.sender is an authorized verifier
        
        userRights[owner][rightId].verified = true;
        userRights[owner][rightId].verifier = msg.sender;
        
        emit RightVerified(owner, rightId, msg.sender);
    }
    
    /**
     * @dev Grant access to a right to a specific viewer
     * @param viewer Address that will have access
     * @param rightId Unique identifier for the right
     * @param expiresAt When access expires (0 for no expiration)
     */
    function grantAccess(address viewer, bytes32 rightId, uint256 expiresAt) external {
        require(userRights[msg.sender][rightId].timestamp > 0, "Right does not exist");
        require(viewer != address(0), "Invalid viewer address");
        
        accessPermissions[msg.sender][viewer][rightId] = AccessPermission({
            hasAccess: true,
            expiresAt: expiresAt,
            lastAccessed: 0
        });
        
        emit AccessGranted(msg.sender, viewer, rightId, expiresAt);
    }
    
    /**
     * @dev Revoke access to a right from a specific viewer
     * @param viewer Address to revoke access from
     * @param rightId Unique identifier for the right
     */
    function revokeAccess(address viewer, bytes32 rightId) external {
        require(userRights[msg.sender][rightId].timestamp > 0, "Right does not exist");
        
        accessPermissions[msg.sender][viewer][rightId].hasAccess = false;
        
        emit AccessRevoked(msg.sender, viewer, rightId);
    }
    
    /**
     * @dev Access a right (if permitted)
     * @param owner Address of the rights owner
     * @param rightId Unique identifier for the right
     * @return encryptedData The encrypted rights data
     */
    function accessRight(address owner, bytes32 rightId) external returns (bytes memory) {
        require(userRights[owner][rightId].timestamp > 0, "Right does not exist");
        
        // If the owner is accessing their own right, always allow
        if (msg.sender == owner) {
            return userRights[owner][rightId].encryptedData;
        }
        
        // Check if viewer has access
        AccessPermission storage permission = accessPermissions[owner][msg.sender][rightId];
        require(permission.hasAccess, "No access permission");
        
        // Check if access hasn't expired
        if (permission.expiresAt > 0) {
            require(block.timestamp <= permission.expiresAt, "Access expired");
        }
        
        // Update last accessed time
        permission.lastAccessed = block.timestamp;
        
        emit RightAccessed(owner, msg.sender, rightId);
        
        return userRights[owner][rightId].encryptedData;
    }
    
    /**
     * @dev Get all rights IDs for a user
     * @param owner Address of the rights owner
     * @return Array of right IDs
     */
    function getRightIds(address owner) external view returns (bytes32[] memory) {
        return userRightsList[owner];
    }
    
    /**
     * @dev Check if a right is verified
     * @param owner Address of the rights owner
     * @param rightId Unique identifier for the right
     * @return Whether the right is verified, and the verifier address
     */
    function isRightVerified(address owner, bytes32 rightId) external view returns (bool, address) {
        EncryptedRight storage right = userRights[owner][rightId];
        return (right.verified, right.verifier);
    }
    
    /**
     * @dev Check if a viewer has access to a right
     * @param owner Address of the rights owner
     * @param viewer Address of the potential viewer
     * @param rightId Unique identifier for the right
     * @return Whether the viewer has access, when access expires, and when it was last accessed
     */
    function checkAccess(address owner, address viewer, bytes32 rightId) external view returns (bool, uint256, uint256) {
        AccessPermission storage permission = accessPermissions[owner][viewer][rightId];
        
        // Check if access hasn't expired
        if (permission.expiresAt > 0 && block.timestamp > permission.expiresAt) {
            return (false, permission.expiresAt, permission.lastAccessed);
        }
        
        return (permission.hasAccess, permission.expiresAt, permission.lastAccessed);
    }
} 