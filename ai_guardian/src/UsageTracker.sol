// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./RightsVault.sol";

/**
 * @title UsageTracker
 * @dev Tracks usage and licensing of rights
 */
contract UsageTracker {
    RightsVault public rightsVault;
    address public owner;
    bool private locked;

    // License types
    enum LicenseType { Commercial, NonCommercial, Personal, Educational }

    // Usage types
    enum UsageType { Streaming, Download, Performance, Remix, Other }

    // Struct for license information
    struct License {
        bytes32 rightsId;
        address licensee;
        LicenseType lType;
        uint256 startTime;
        uint256 endTime;
        uint256 maxUses;
        uint256 currentUses;
        bool isActive;
        uint256 fee;
    }

    // Struct for usage record
    struct UsageRecord {
        bytes32 rightsId;
        address user;
        UsageType uType;
        uint256 timestamp;
        string metadata;
    }

    // Mapping from license ID to License
    mapping(bytes32 => License) public licenses;
    
    // Mapping from rights ID to array of license IDs
    mapping(bytes32 => bytes32[]) public rightsLicenses;
    
    // Mapping from usage ID to UsageRecord
    mapping(bytes32 => UsageRecord) public usageRecords;
    
    // Mapping from rights ID to array of usage IDs
    mapping(bytes32 => bytes32[]) public rightsUsageRecords;
    
    // Events
    event LicenseCreated(
        bytes32 indexed licenseId,
        bytes32 indexed rightsId,
        address indexed licensee,
        LicenseType lType
    );
    event LicenseUpdated(bytes32 indexed licenseId);
    event LicenseRevoked(bytes32 indexed licenseId);
    event UsageRecorded(
        bytes32 indexed usageId,
        bytes32 indexed rightsId,
        address indexed user,
        UsageType uType
    );

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

    constructor(address _rightsVault) {
        owner = msg.sender;
        rightsVault = RightsVault(_rightsVault);
        locked = false;
    }

    /**
     * @dev Create a new license
     * @param rightsId Rights identifier
     * @param licensee Address of the licensee
     * @param lType Type of license
     * @param startTime Start time of the license
     * @param endTime End time of the license
     * @param maxUses Maximum number of uses allowed
     * @param fee License fee in wei
     * @return licenseId Unique identifier for the license
     */
    function createLicense(
        bytes32 rightsId,
        address licensee,
        LicenseType lType,
        uint256 startTime,
        uint256 endTime,
        uint256 maxUses,
        uint256 fee
    ) external nonReentrant returns (bytes32) {
        require(endTime > startTime, "Invalid time range");
        require(maxUses > 0, "Invalid max uses");

        bytes32 licenseId = keccak256(
            abi.encodePacked(
                rightsId,
                licensee,
                lType,
                startTime,
                endTime,
                maxUses,
                fee,
                block.timestamp
            )
        );

        licenses[licenseId] = License({
            rightsId: rightsId,
            licensee: licensee,
            lType: lType,
            startTime: startTime,
            endTime: endTime,
            maxUses: maxUses,
            currentUses: 0,
            isActive: true,
            fee: fee
        });

        rightsLicenses[rightsId].push(licenseId);

        emit LicenseCreated(licenseId, rightsId, licensee, lType);
        return licenseId;
    }

    /**
     * @dev Record usage of rights
     * @param rightsId Rights identifier
     * @param uType Type of usage
     * @param metadata Additional usage metadata
     * @return usageId Unique identifier for the usage record
     */
    function recordUsage(
        bytes32 rightsId,
        UsageType uType,
        string calldata metadata
    ) external nonReentrant returns (bytes32) {
        bytes32 usageId = keccak256(
            abi.encodePacked(
                rightsId,
                msg.sender,
                uType,
                block.timestamp,
                metadata
            )
        );

        usageRecords[usageId] = UsageRecord({
            rightsId: rightsId,
            user: msg.sender,
            uType: uType,
            timestamp: block.timestamp,
            metadata: metadata
        });

        rightsUsageRecords[rightsId].push(usageId);

        emit UsageRecorded(usageId, rightsId, msg.sender, uType);
        return usageId;
    }

    /**
     * @dev Update a license
     * @param licenseId License identifier
     * @param endTime New end time
     * @param maxUses New maximum uses
     * @param fee New license fee
     */
    function updateLicense(
        bytes32 licenseId,
        uint256 endTime,
        uint256 maxUses,
        uint256 fee
    ) external nonReentrant {
        License storage license = licenses[licenseId];
        require(license.isActive, "License not active");
        require(endTime > block.timestamp, "Invalid end time");
        require(maxUses >= license.currentUses, "Invalid max uses");

        license.endTime = endTime;
        license.maxUses = maxUses;
        license.fee = fee;

        emit LicenseUpdated(licenseId);
    }

    /**
     * @dev Revoke a license
     * @param licenseId License identifier
     */
    function revokeLicense(bytes32 licenseId) external nonReentrant {
        License storage license = licenses[licenseId];
        require(license.isActive, "License not active");
        
        license.isActive = false;
        
        emit LicenseRevoked(licenseId);
    }

    /**
     * @dev Get license data
     * @param licenseId License identifier
     * @return License struct containing the license information
     */
    function getLicenseData(bytes32 licenseId) external view returns (License memory) {
        return licenses[licenseId];
    }

    /**
     * @dev Get all licenses for specific rights
     * @param rightsId Rights identifier
     * @return Array of license IDs
     */
    function getRightsLicenses(bytes32 rightsId) external view returns (bytes32[] memory) {
        return rightsLicenses[rightsId];
    }

    /**
     * @dev Get usage record data
     * @param usageId Usage record identifier
     * @return UsageRecord struct containing the usage information
     */
    function getUsageRecord(bytes32 usageId) external view returns (UsageRecord memory) {
        return usageRecords[usageId];
    }

    /**
     * @dev Get all usage records for specific rights
     * @param rightsId Rights identifier
     * @return Array of usage record IDs
     */
    function getRightsUsageRecords(bytes32 rightsId) external view returns (bytes32[] memory) {
        return rightsUsageRecords[rightsId];
    }

    /**
     * @dev Check if a license is valid for usage
     * @param licenseId License identifier
     * @return bool Whether the license is valid
     */
    function isLicenseValid(bytes32 licenseId) external view returns (bool) {
        License storage license = licenses[licenseId];
        return license.isActive &&
               block.timestamp >= license.startTime &&
               block.timestamp <= license.endTime &&
               license.currentUses < license.maxUses;
    }
} 