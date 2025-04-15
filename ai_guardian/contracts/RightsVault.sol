// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

/**
 * @title RightsVault
 * @dev Smart contract for storing and managing music rights data with privacy controls
 */
contract RightsVault {
    // Storage for encrypted rights references
    mapping(address => mapping(bytes32 => EncryptedRight)) private userRights;
    
    struct EncryptedRight {
        bytes encryptedData;
        bytes32 dataHash;
        uint256 timestamp;
        bool verified;
    }
    
    // Access control mapping
    mapping(address => mapping(address => mapping(bytes32 => bool))) private accessPermissions;
    
    // Events
    event RightRegistered(address indexed owner, bytes32 indexed rightId);
    event RightUpdated(address indexed owner, bytes32 indexed rightId);
    event AccessGranted(address indexed owner, address indexed viewer, bytes32 indexed rightId);
    event AccessRevoked(address indexed owner, address indexed viewer, bytes32 indexed rightId);
    
    /**
     * @dev Register a new right with encrypted data
     * @param rightId Unique identifier for the right
     * @param encryptedData Encrypted rights data
     */
    function registerRight(bytes32 rightId, bytes calldata encryptedData) external {
        require(userRights[msg.sender][rightId].timestamp == 0, "Right already exists");
        
        userRights[msg.sender][rightId] = EncryptedRight({
            encryptedData: encryptedData,
            dataHash: keccak256(encryptedData),
            timestamp: block.timestamp,
            verified: false
        });
        
        emit RightRegistered(msg.sender, rightId);
    }
    
    /**
     * @dev Update an existing right
     * @param rightId Unique identifier for the right
     * @param encryptedData New encrypted rights data
     */
    function updateRight(bytes32 rightId, bytes calldata encryptedData) external {
        require(userRights[msg.sender][rightId].timestamp > 0, "Right does not exist");
        
        userRights[msg.sender][rightId].encryptedData = encryptedData;
        userRights[msg.sender][rightId].dataHash = keccak256(encryptedData);
        userRights[msg.sender][rightId].timestamp = block.timestamp;
        
        emit RightUpdated(msg.sender, rightId);
    }
    
    /**
     * @dev Grant access to a specific right to another address
     * @param viewer Address to grant access to
     * @param rightId Unique identifier for the right
     */
    function grantAccess(address viewer, bytes32 rightId) external {
        require(userRights[msg.sender][rightId].timestamp > 0, "Right does not exist");
        require(!accessPermissions[msg.sender][viewer][rightId], "Access already granted");
        
        accessPermissions[msg.sender][viewer][rightId] = true;
        
        emit AccessGranted(msg.sender, viewer, rightId);
    }
    
    /**
     * @dev Revoke access to a specific right from another address
     * @param viewer Address to revoke access from
     * @param rightId Unique identifier for the right
     */
    function revokeAccess(address viewer, bytes32 rightId) external {
        require(userRights[msg.sender][rightId].timestamp > 0, "Right does not exist");
        require(accessPermissions[msg.sender][viewer][rightId], "Access not granted");
        
        accessPermissions[msg.sender][viewer][rightId] = false;
        
        emit AccessRevoked(msg.sender, viewer, rightId);
    }
    
    /**
     * @dev Check if a viewer has access to a specific right
     * @param owner Address of the right owner
     * @param viewer Address of the potential viewer
     * @param rightId Unique identifier for the right
     * @return Boolean indicating whether access is granted
     */
    function hasAccess(address owner, address viewer, bytes32 rightId) external view returns (bool) {
        return accessPermissions[owner][viewer][rightId];
    }
    
    /**
     * @dev Get the data hash of a right
     * @param owner Address of the right owner
     * @param rightId Unique identifier for the right
     * @return Data hash of the right
     */
    function getRightDataHash(address owner, bytes32 rightId) external view returns (bytes32) {
        require(userRights[owner][rightId].timestamp > 0, "Right does not exist");
        require(owner == msg.sender || accessPermissions[owner][msg.sender][rightId], "Not authorized");
        
        return userRights[owner][rightId].dataHash;
    }
    
    /**
     * @dev Get the encrypted data of a right
     * @param owner Address of the right owner
     * @param rightId Unique identifier for the right
     * @return Encrypted data of the right
     */
    function getRightData(address owner, bytes32 rightId) external view returns (bytes memory) {
        require(userRights[owner][rightId].timestamp > 0, "Right does not exist");
        require(owner == msg.sender || accessPermissions[owner][msg.sender][rightId], "Not authorized");
        
        return userRights[owner][rightId].encryptedData;
    }
    
    /**
     * @dev Set the verification status of a right
     * @param rightId Unique identifier for the right
     * @param verified New verification status
     */
    function setVerificationStatus(bytes32 rightId, bool verified) external {
        require(userRights[msg.sender][rightId].timestamp > 0, "Right does not exist");
        
        userRights[msg.sender][rightId].verified = verified;
    }
    
    /**
     * @dev Check if a right is verified
     * @param owner Address of the right owner
     * @param rightId Unique identifier for the right
     * @return Boolean indicating whether the right is verified
     */
    function isRightVerified(address owner, bytes32 rightId) external view returns (bool) {
        require(userRights[owner][rightId].timestamp > 0, "Right does not exist");
        
        return userRights[owner][rightId].verified;
    }
    
    /**
     * @dev Get the timestamp when a right was last updated
     * @param owner Address of the right owner
     * @param rightId Unique identifier for the right
     * @return Timestamp of the last update
     */
    function getRightTimestamp(address owner, bytes32 rightId) external view returns (uint256) {
        require(userRights[owner][rightId].timestamp > 0, "Right does not exist");
        
        return userRights[owner][rightId].timestamp;
    }
} 