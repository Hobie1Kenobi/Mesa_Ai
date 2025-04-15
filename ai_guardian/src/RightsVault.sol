// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title RightsVault
 * @dev Core contract for storing and managing rights data with privacy features
 */
contract RightsVault {
    address public owner;
    bool private locked;

    // Struct to store rights data
    struct RightsData {
        bytes32 encryptedData;      // Encrypted rights data
        bytes32 dataHash;           // Hash of the original data
        address rightsOwner;        // Address of the rights owner
        uint256 timestamp;          // Timestamp of registration
        bool isActive;              // Whether the rights are active
    }

    // Mapping from rights ID to RightsData
    mapping(bytes32 => RightsData) public rightsRegistry;
    
    // Mapping from rights owner to their rights IDs
    mapping(address => bytes32[]) public ownerRights;
    
    // Events
    event RightsRegistered(bytes32 indexed rightsId, address indexed owner, uint256 timestamp);
    event RightsUpdated(bytes32 indexed rightsId, address indexed owner);
    event RightsDeactivated(bytes32 indexed rightsId);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier nonReentrant() {
        require(!locked, "Reentrant call");
        locked = true;
        _;
        locked = false;
    }

    constructor() {
        owner = msg.sender;
        locked = false;
    }

    /**
     * @dev Register new rights data
     * @param rightsId Unique identifier for the rights
     * @param encryptedData Encrypted rights data
     * @param dataHash Hash of the original data
     */
    function registerRights(
        bytes32 rightsId,
        bytes32 encryptedData,
        bytes32 dataHash
    ) public virtual nonReentrant {
        require(rightsRegistry[rightsId].timestamp == 0, "Rights already registered");
        
        rightsRegistry[rightsId] = RightsData({
            encryptedData: encryptedData,
            dataHash: dataHash,
            rightsOwner: msg.sender,
            timestamp: block.timestamp,
            isActive: true
        });
        
        ownerRights[msg.sender].push(rightsId);
        
        emit RightsRegistered(rightsId, msg.sender, block.timestamp);
    }

    /**
     * @dev Update existing rights data
     * @param rightsId Rights identifier to update
     * @param encryptedData New encrypted rights data
     * @param dataHash New hash of the original data
     */
    function updateRights(
        bytes32 rightsId,
        bytes32 encryptedData,
        bytes32 dataHash
    ) external nonReentrant {
        require(rightsRegistry[rightsId].rightsOwner == msg.sender, "Not rights owner");
        require(rightsRegistry[rightsId].isActive, "Rights not active");
        
        rightsRegistry[rightsId].encryptedData = encryptedData;
        rightsRegistry[rightsId].dataHash = dataHash;
        
        emit RightsUpdated(rightsId, msg.sender);
    }

    /**
     * @dev Deactivate rights
     * @param rightsId Rights identifier to deactivate
     */
    function deactivateRights(bytes32 rightsId) external nonReentrant {
        require(rightsRegistry[rightsId].rightsOwner == msg.sender, "Not rights owner");
        require(rightsRegistry[rightsId].isActive, "Rights already inactive");
        
        rightsRegistry[rightsId].isActive = false;
        
        emit RightsDeactivated(rightsId);
    }

    /**
     * @dev Get rights data
     * @param rightsId Rights identifier
     * @return RightsData struct containing the rights information
     */
    function getRightsData(bytes32 rightsId) external view returns (RightsData memory) {
        return rightsRegistry[rightsId];
    }

    /**
     * @dev Get all rights IDs for an owner
     * @param _owner Address of the rights owner
     * @return Array of rights IDs
     */
    function getOwnerRights(address _owner) public view virtual returns (bytes32[] memory) {
        return ownerRights[_owner];
    }
} 