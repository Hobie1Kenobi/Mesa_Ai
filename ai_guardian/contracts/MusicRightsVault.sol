// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

contract MusicRightsVault {
    struct MusicRight {
        string rightId;
        address rightsHolder;
        string rightsType;
        uint256 percentage;  // in basis points (1% = 100)
        string territory;
        string startDate;
        string endDate;
        bytes32 metadataHash;
        bool isActive;
    }
    
    // Mapping from rightId to MusicRight
    mapping(string => MusicRight) private rights;
    
    // Mapping from rightsHolder to their rightIds
    mapping(address => string[]) private holderRights;
    
    // Events
    event RightRegistered(string indexed rightId, address indexed rightsHolder);
    event RightUpdated(string indexed rightId, address indexed rightsHolder);
    event RightDeactivated(string indexed rightId, address indexed rightsHolder);
    
    // Modifiers
    modifier onlyRightsHolder(string memory rightId) {
        require(rights[rightId].rightsHolder == msg.sender, "Not the rights holder");
        _;
    }
    
    modifier rightExists(string memory rightId) {
        require(rights[rightId].isActive, "Right does not exist or is inactive");
        _;
    }
    
    // Core functions
    function registerRight(
        string memory rightId,
        string memory rightsType,
        uint256 percentage,
        string memory territory,
        string memory startDate,
        string memory endDate,
        bytes32 metadataHash
    ) external {
        require(rights[rightId].rightsHolder == address(0), "Right already exists");
        require(percentage <= 10000, "Percentage must be <= 100%");
        
        rights[rightId] = MusicRight({
            rightId: rightId,
            rightsHolder: msg.sender,
            rightsType: rightsType,
            percentage: percentage,
            territory: territory,
            startDate: startDate,
            endDate: endDate,
            metadataHash: metadataHash,
            isActive: true
        });
        
        holderRights[msg.sender].push(rightId);
        
        emit RightRegistered(rightId, msg.sender);
    }
    
    function updateRight(
        string memory rightId,
        uint256 percentage,
        string memory territory,
        string memory endDate,
        bytes32 metadataHash
    ) external onlyRightsHolder(rightId) rightExists(rightId) {
        require(percentage <= 10000, "Percentage must be <= 100%");
        
        MusicRight storage right = rights[rightId];
        right.percentage = percentage;
        right.territory = territory;
        right.endDate = endDate;
        right.metadataHash = metadataHash;
        
        emit RightUpdated(rightId, msg.sender);
    }
    
    function deactivateRight(string memory rightId) 
        external 
        onlyRightsHolder(rightId) 
        rightExists(rightId) 
    {
        rights[rightId].isActive = false;
        emit RightDeactivated(rightId, msg.sender);
    }
    
    // View functions
    function getRight(string memory rightId) 
        external 
        view 
        rightExists(rightId) 
        returns (
            address rightsHolder,
            string memory rightsType,
            uint256 percentage,
            string memory territory,
            string memory startDate,
            string memory endDate,
            bytes32 metadataHash
        ) 
    {
        MusicRight memory right = rights[rightId];
        return (
            right.rightsHolder,
            right.rightsType,
            right.percentage,
            right.territory,
            right.startDate,
            right.endDate,
            right.metadataHash
        );
    }
    
    function getHolderRights(address holder) 
        external 
        view 
        returns (string[] memory) 
    {
        return holderRights[holder];
    }
    
    function verifyRight(string memory rightId) 
        external 
        view 
        returns (bool) 
    {
        return rights[rightId].isActive;
    }
} 