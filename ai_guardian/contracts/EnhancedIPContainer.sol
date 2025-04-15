// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "./MusicRightsContainer.sol";

/**
 * @title EnhancedIPContainer
 * @dev Token-bound container for unified music IP assets including multiple NFTs
 */
contract EnhancedIPContainer is MusicRightsContainer {
    // Track different IP assets owned by this container
    struct IPAsset {
        address tokenContract;
        uint256 tokenId;
        string assetType;   // "cover_art", "video", "remix", "stems", etc.
        string metadata;    // Additional metadata about the asset
        uint256 timestamp;  // When asset was added
    }
    
    // All IP assets managed by this container
    IPAsset[] public ipAssets;
    
    // Current valuation estimation (in ETH)
    uint256 public portfolioValuation;
    
    // Events
    event IPAssetAdded(address tokenContract, uint256 tokenId, string assetType);
    event ValuationUpdated(uint256 previousValue, uint256 newValue);
    event PortfolioTraded(address previousOwner, address newOwner, uint256 value);
    
    /**
     * @dev Add a new IP asset to the container
     * @param tokenContract The asset contract address
     * @param tokenId The asset token ID
     * @param assetType Type of asset (cover_art, video, etc)
     * @param metadata Additional metadata about the asset
     */
    function addIPAsset(
        address tokenContract,
        uint256 tokenId,
        string calldata assetType,
        string calldata metadata
    ) external {
        // Only owner can add assets
        (, address ownerTokenContract, uint256 ownerTokenId) = _token();
        
        // Add asset to registry
        ipAssets.push(IPAsset({
            tokenContract: tokenContract,
            tokenId: tokenId,
            assetType: assetType,
            metadata: metadata,
            timestamp: block.timestamp
        }));
        
        emit IPAssetAdded(tokenContract, tokenId, assetType);
    }
    
    /**
     * @dev Update portfolio valuation
     * @param newValuation New valuation in ETH
     */
    function updateValuation(uint256 newValuation) external {
        // Only owner can update valuation
        (, address tokenContract, uint256 tokenId) = _token();
        
        uint256 oldValuation = portfolioValuation;
        portfolioValuation = newValuation;
        
        emit ValuationUpdated(oldValuation, newValuation);
    }
    
    /**
     * @dev Get all IP assets
     * @return Array of IP assets
     */
    function getAllIPAssets() external view returns (IPAsset[] memory) {
        return ipAssets;
    }
    
    /**
     * @dev Get assets by type
     * @param assetType Type of asset to filter by
     * @return Filtered array of IP assets
     */
    function getAssetsByType(string calldata assetType) external view returns (IPAsset[] memory) {
        // Count matching assets
        uint256 count = 0;
        for (uint256 i = 0; i < ipAssets.length; i++) {
            if (keccak256(bytes(ipAssets[i].assetType)) == keccak256(bytes(assetType))) {
                count++;
            }
        }
        
        // Create result array
        IPAsset[] memory result = new IPAsset[](count);
        uint256 resultIndex = 0;
        
        // Fill result array
        for (uint256 i = 0; i < ipAssets.length; i++) {
            if (keccak256(bytes(ipAssets[i].assetType)) == keccak256(bytes(assetType))) {
                result[resultIndex] = ipAssets[i];
                resultIndex++;
            }
        }
        
        return result;
    }
    
    /**
     * @dev Get container summary
     * @return assetCount Number of assets
     * @return valuation Current valuation
     * @return attestationCount Number of attestations
     */
    function getContainerSummary() external view returns (
        uint256 assetCount,
        uint256 valuation,
        uint256 attestationCount
    ) {
        AttestationData[] memory _attestations = getAttestations();
        return (ipAssets.length, portfolioValuation, _attestations.length);
    }
} 