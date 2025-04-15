// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC1155/extensions/ERC1155URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title MusicVideoNFT
 * @dev ERC-1155 token representing music videos and other editions
 */
contract MusicVideoNFT is ERC1155URIStorage, Ownable {
    // Counter for token IDs
    uint256 private _nextTokenId = 1;
    
    // Edition types
    enum EditionType { MusicVideo, Visualizer, LivePerformance, Remix, BehindTheScenes }
    
    // Additional metadata for video editions
    struct VideoMetadata {
        string title;
        string artist;
        string workReference;    // Reference to the original musical work
        EditionType editionType; // Type of video
        uint256 duration;        // Duration in seconds
        uint256 creationDate;    // Timestamp when created
        uint256 maxSupply;       // Maximum supply (0 for unlimited)
        string videoFormat;      // e.g., "mp4", "webm", etc.
        string resolution;       // e.g., "1080p", "4K", etc.
    }
    
    // Mapping for video metadata
    mapping(uint256 => VideoMetadata) private _metadata;
    
    // Events
    event VideoEditionCreated(uint256 indexed tokenId, string title, EditionType editionType);
    event EditionMinted(uint256 indexed tokenId, address indexed to, uint256 amount);
    
    /**
     * @dev Constructor
     */
    constructor() ERC1155("") Ownable(msg.sender) {}
    
    /**
     * @dev Create a new video edition
     * @param title The title of the work
     * @param artist The artist name
     * @param workReference Reference to the musical work
     * @param editionType Type of video edition
     * @param duration Duration in seconds
     * @param maxSupply Maximum supply (0 for unlimited)
     * @param videoFormat Format of the video
     * @param resolution Resolution of the video
     * @param uri URI for token metadata
     * @return tokenId The ID of the created token
     */
    function createVideoEdition(
        string calldata title,
        string calldata artist,
        string calldata workReference,
        EditionType editionType,
        uint256 duration,
        uint256 maxSupply,
        string calldata videoFormat,
        string calldata resolution,
        string calldata uri
    ) external onlyOwner returns (uint256) {
        uint256 tokenId = _nextTokenId++;
        
        _setURI(tokenId, uri);
        
        _metadata[tokenId] = VideoMetadata({
            title: title,
            artist: artist,
            workReference: workReference,
            editionType: editionType,
            duration: duration,
            creationDate: block.timestamp,
            maxSupply: maxSupply,
            videoFormat: videoFormat,
            resolution: resolution
        });
        
        emit VideoEditionCreated(tokenId, title, editionType);
        
        return tokenId;
    }
    
    /**
     * @dev Mint tokens of a video edition
     * @param to The address to mint to
     * @param tokenId The ID of the token
     * @param amount The amount to mint
     * @param data Additional data
     */
    function mintEdition(
        address to,
        uint256 tokenId,
        uint256 amount,
        bytes calldata data
    ) external onlyOwner {
        require(tokenId < _nextTokenId, "Token does not exist");
        
        // Check max supply if set
        if (_metadata[tokenId].maxSupply > 0) {
            require(
                totalSupply(tokenId) + amount <= _metadata[tokenId].maxSupply,
                "Would exceed max supply"
            );
        }
        
        _mint(to, tokenId, amount, data);
        
        emit EditionMinted(tokenId, to, amount);
    }
    
    /**
     * @dev Get metadata for a video token
     * @param tokenId The ID of the token
     * @return Metadata struct
     */
    function getVideoMetadata(uint256 tokenId) external view returns (VideoMetadata memory) {
        require(tokenId < _nextTokenId, "Token does not exist");
        return _metadata[tokenId];
    }
    
    /**
     * @dev Get total supply of a token
     * @param tokenId The ID of the token
     * @return The total supply
     */
    function totalSupply(uint256 tokenId) public view returns (uint256) {
        // This is simplified and would need proper tracking in production
        return 0; // Placeholder
    }
} 