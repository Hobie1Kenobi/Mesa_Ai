// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title CoverArtNFT
 * @dev ERC-721 token representing exclusive music cover art
 */
contract CoverArtNFT is ERC721URIStorage, Ownable {
    // Counter for token IDs
    uint256 private _nextTokenId = 1;
    
    // Additional metadata for cover art
    struct CoverArtMetadata {
        string title;
        string artist;
        string workReference;  // Reference to the original musical work
        string imageFormat;    // e.g., "jpg", "png", etc.
        uint256 creationDate;  // Timestamp when created
        bool isOfficial;       // Whether this is the official cover
    }
    
    // Mapping for cover art metadata
    mapping(uint256 => CoverArtMetadata) private _metadata;
    
    // Events
    event CoverArtMinted(uint256 indexed tokenId, string title, string artist);
    
    /**
     * @dev Constructor
     */
    constructor() ERC721("Music Cover Art", "MCOVER") Ownable(msg.sender) {}
    
    /**
     * @dev Mint a new cover art NFT
     * @param to The address to mint to
     * @param title The title of the work
     * @param artist The artist name
     * @param workReference Reference to the musical work
     * @param imageFormat Format of the image
     * @param isOfficial Whether this is the official cover
     * @param tokenURI URI for token metadata
     * @return tokenId The ID of the minted token
     */
    function mintCoverArt(
        address to,
        string calldata title,
        string calldata artist,
        string calldata workReference,
        string calldata imageFormat,
        bool isOfficial,
        string calldata tokenURI
    ) external onlyOwner returns (uint256) {
        uint256 tokenId = _nextTokenId++;
        
        _mint(to, tokenId);
        _setTokenURI(tokenId, tokenURI);
        
        _metadata[tokenId] = CoverArtMetadata({
            title: title,
            artist: artist,
            workReference: workReference,
            imageFormat: imageFormat,
            creationDate: block.timestamp,
            isOfficial: isOfficial
        });
        
        emit CoverArtMinted(tokenId, title, artist);
        
        return tokenId;
    }
    
    /**
     * @dev Get metadata for a cover art token
     * @param tokenId The ID of the token
     * @return Metadata struct
     */
    function getCoverArtMetadata(uint256 tokenId) external view returns (CoverArtMetadata memory) {
        require(_exists(tokenId), "CoverArtNFT: Query for nonexistent token");
        return _metadata[tokenId];
    }
    
    /**
     * @dev Check if a token exists
     * @param tokenId The ID of the token
     * @return Whether the token exists
     */
    function _exists(uint256 tokenId) internal view returns (bool) {
        return _ownerOf(tokenId) != address(0);
    }
} 