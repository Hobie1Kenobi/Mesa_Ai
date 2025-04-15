// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./RightsVault.sol";

/**
 * @title RoyaltyManager
 * @dev Manages royalty distributions for music rights
 */
contract RoyaltyManager {
    RightsVault public rightsVault;
    address public owner;
    bool private locked;

    // Struct for royalty split information
    struct RoyaltySplit {
        address payable recipient;
        uint256 sharePercentage;  // Base 10000 (e.g., 2500 = 25%)
        bool isActive;
    }

    // Mapping from rights ID to array of royalty splits
    mapping(bytes32 => RoyaltySplit[]) public royaltySplits;
    
    // Mapping to track total shares for each rights ID
    mapping(bytes32 => uint256) public totalShares;
    
    // Events
    event RoyaltySplitAdded(bytes32 indexed rightsId, address indexed recipient, uint256 sharePercentage);
    event RoyaltyDistributed(bytes32 indexed rightsId, uint256 amount);
    event RoyaltySplitUpdated(bytes32 indexed rightsId, address indexed recipient, uint256 newSharePercentage);
    event RoyaltySplitRemoved(bytes32 indexed rightsId, address indexed recipient);

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

    modifier onlyRightsOwner(bytes32 rightsId) {
        require(rightsVault.getRightsData(rightsId).rightsOwner == msg.sender, "Not rights owner");
        _;
    }

    constructor(address _rightsVault) {
        owner = msg.sender;
        rightsVault = RightsVault(_rightsVault);
        locked = false;
    }

    /**
     * @dev Add a new royalty split for rights
     * @param rightsId Rights identifier
     * @param recipient Address to receive royalties
     * @param sharePercentage Share percentage (base 10000)
     */
    function addRoyaltySplit(
        bytes32 rightsId,
        address payable recipient,
        uint256 sharePercentage
    ) external onlyRightsOwner(rightsId) nonReentrant {
        require(sharePercentage > 0 && sharePercentage <= 10000, "Invalid share percentage");
        require(totalShares[rightsId] + sharePercentage <= 10000, "Total shares exceed 100%");
        
        royaltySplits[rightsId].push(RoyaltySplit({
            recipient: recipient,
            sharePercentage: sharePercentage,
            isActive: true
        }));
        
        totalShares[rightsId] += sharePercentage;
        
        emit RoyaltySplitAdded(rightsId, recipient, sharePercentage);
    }

    /**
     * @dev Update an existing royalty split
     * @param rightsId Rights identifier
     * @param recipientIndex Index of the recipient in the splits array
     * @param newSharePercentage New share percentage
     */
    function updateRoyaltySplit(
        bytes32 rightsId,
        uint256 recipientIndex,
        uint256 newSharePercentage
    ) external onlyRightsOwner(rightsId) nonReentrant {
        require(recipientIndex < royaltySplits[rightsId].length, "Invalid recipient index");
        require(newSharePercentage > 0 && newSharePercentage <= 10000, "Invalid share percentage");
        
        RoyaltySplit storage split = royaltySplits[rightsId][recipientIndex];
        require(split.isActive, "Split not active");
        
        uint256 oldShare = split.sharePercentage;
        require(totalShares[rightsId] - oldShare + newSharePercentage <= 10000, "Total shares exceed 100%");
        
        totalShares[rightsId] = totalShares[rightsId] - oldShare + newSharePercentage;
        split.sharePercentage = newSharePercentage;
        
        emit RoyaltySplitUpdated(rightsId, split.recipient, newSharePercentage);
    }

    /**
     * @dev Remove a royalty split
     * @param rightsId Rights identifier
     * @param recipientIndex Index of the recipient in the splits array
     */
    function removeRoyaltySplit(
        bytes32 rightsId,
        uint256 recipientIndex
    ) external onlyRightsOwner(rightsId) nonReentrant {
        require(recipientIndex < royaltySplits[rightsId].length, "Invalid recipient index");
        
        RoyaltySplit storage split = royaltySplits[rightsId][recipientIndex];
        require(split.isActive, "Split not active");
        
        totalShares[rightsId] -= split.sharePercentage;
        split.isActive = false;
        
        emit RoyaltySplitRemoved(rightsId, split.recipient);
    }

    /**
     * @dev Distribute royalties to all recipients
     * @param rightsId Rights identifier
     */
    function distributeRoyalties(bytes32 rightsId) external payable nonReentrant {
        require(msg.value > 0, "No royalties to distribute");
        require(totalShares[rightsId] > 0, "No royalty splits defined");
        
        uint256 remainingAmount = msg.value;
        RoyaltySplit[] storage splits = royaltySplits[rightsId];
        
        for (uint256 i = 0; i < splits.length; i++) {
            if (splits[i].isActive) {
                uint256 share = (msg.value * splits[i].sharePercentage) / 10000;
                remainingAmount -= share;
                
                (bool success, ) = splits[i].recipient.call{value: share}("");
                require(success, "Transfer failed");
            }
        }
        
        // Return any remaining dust to the sender
        if (remainingAmount > 0) {
            (bool success, ) = msg.sender.call{value: remainingAmount}("");
            require(success, "Refund failed");
        }
        
        emit RoyaltyDistributed(rightsId, msg.value);
    }

    /**
     * @dev Get all royalty splits for rights
     * @param rightsId Rights identifier
     * @return Array of active royalty splits
     */
    function getRoyaltySplits(bytes32 rightsId) external view returns (RoyaltySplit[] memory) {
        return royaltySplits[rightsId];
    }

    /**
     * @dev Get total shares for rights
     * @param rightsId Rights identifier
     * @return Total share percentage
     */
    function getTotalShares(bytes32 rightsId) external view returns (uint256) {
        return totalShares[rightsId];
    }

    // Allow contract to receive ETH
    receive() external payable {}
} 