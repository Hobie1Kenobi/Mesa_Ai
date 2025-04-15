// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title MusicRightsNFT
 * @dev ERC-721 token representing music rights
 */
contract MusicRightsNFT is ERC721Enumerable, Ownable {
    // Counter for token IDs
    uint256 private _nextTokenId = 1;
    
    // Token metadata
    mapping(uint256 => string) private _tokenURIs;
    
    // Rights data
    struct RightsMetadata {
        string contractId;      // Reference to traditional contract
        string rightsType;      // Type of rights (composition, recording, etc.)
        string territory;       // Territory covered
        uint256 timestamp;      // When token was minted
    }
    
    mapping(uint256 => RightsMetadata) private _rightsData;
    
    // Events
    event RightsMinted(address indexed to, uint256 indexed tokenId, string contractId);
    
    /**
     * @dev Constructor
     */
    constructor() ERC721("Music Rights NFT", "MRIGHT") Ownable(msg.sender) {}
    
    /**
     * @dev Mint a new music rights NFT
     * @param to The address that will own the NFT
     * @param contractId Reference to traditional contract
     * @param rightsType Type of rights
     * @param territory Territory covered
     * @param tokenURI Metadata URI
     * @return tokenId The ID of the minted token
     */
    function mintRights(
        address to,
        string calldata contractId,
        string calldata rightsType,
        string calldata territory,
        string calldata tokenURI
    ) external onlyOwner returns (uint256) {
        uint256 tokenId = _nextTokenId++;
        
        _mint(to, tokenId);
        _setTokenURI(tokenId, tokenURI);
        
        _rightsData[tokenId] = RightsMetadata({
            contractId: contractId,
            rightsType: rightsType,
            territory: territory,
            timestamp: block.timestamp
        });
        
        emit RightsMinted(to, tokenId, contractId);
        
        return tokenId;
    }
    
    /**
     * @dev Returns rights metadata for a token
     * @param tokenId The ID of the token
     * @return RightsMetadata struct
     */
    function getRightsData(uint256 tokenId) external view returns (RightsMetadata memory) {
        _requireMinted(tokenId);
        return _rightsData[tokenId];
    }
    
    /**
     * @dev Returns the metadata URI for a token
     * @param tokenId The ID of the token
     * @return Token URI string
     */
    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        _requireMinted(tokenId);
        return _tokenURIs[tokenId];
    }
    
    /**
     * @dev Sets the token URI for a token
     * @param tokenId The ID of the token
     * @param tokenURI_ The new token URI
     */
    function _setTokenURI(uint256 tokenId, string memory tokenURI_) internal {
        _tokenURIs[tokenId] = tokenURI_;
    }
} 