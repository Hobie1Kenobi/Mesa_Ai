// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title MusicRightsVault
 * @dev A contract for managing privacy-first portable music rights on Base
 * This contract enables musicians to verify and manage their music rights while 
 * maintaining privacy through zero-knowledge proofs.
 */
contract MusicRightsVault {
    // Owner of the contract
    address public owner;
    
    // Mapping of right ID to its metadata hash
    mapping(bytes32 => bytes32) private rightMetadataHashes;
    
    // Mapping of rights IDs owned by address (privacy layer)
    mapping(address => bytes32[]) private rightsOwned;
    
    // Mapping of right ID to verification status
    mapping(bytes32 => bool) private rightsVerified;
    
    // Mapping of authorized verifiers
    mapping(address => bool) public authorizedVerifiers;
    
    // Event emitted when a new right is registered
    event RightRegistered(bytes32 indexed rightId, address indexed owner);
    
    // Event emitted when a right is verified
    event RightVerified(bytes32 indexed rightId, address indexed verifier);
    
    // Event emitted when a right is transferred
    event RightTransferred(bytes32 indexed rightId, address indexed from, address indexed to);
    
    // Event emitted when a verifier is added or removed
    event VerifierStatusChanged(address indexed verifier, bool status);

    /**
     * @dev Constructor that sets the owner of the contract
     */
    constructor() {
        owner = msg.sender;
        authorizedVerifiers[msg.sender] = true;
    }
    
    /**
     * @dev Modifier to restrict function access to the contract owner
     */
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    /**
     * @dev Modifier to restrict function access to authorized verifiers
     */
    modifier onlyVerifier() {
        require(authorizedVerifiers[msg.sender], "Only authorized verifiers can call this function");
        _;
    }
    
    /**
     * @dev Add a verifier to the authorized list
     * @param verifier Address of the verifier to authorize
     */
    function addVerifier(address verifier) external onlyOwner {
        require(verifier != address(0), "Invalid verifier address");
        authorizedVerifiers[verifier] = true;
        emit VerifierStatusChanged(verifier, true);
    }
    
    /**
     * @dev Remove a verifier from the authorized list
     * @param verifier Address of the verifier to remove
     */
    function removeVerifier(address verifier) external onlyOwner {
        require(authorizedVerifiers[verifier], "Address is not a verifier");
        authorizedVerifiers[verifier] = false;
        emit VerifierStatusChanged(verifier, false);
    }
    
    /**
     * @dev Register a new music right
     * @param rightId Unique identifier for the right
     * @param metadataHash Hash of metadata associated with the right (stored off-chain)
     */
    function registerRight(bytes32 rightId, bytes32 metadataHash) external {
        require(rightMetadataHashes[rightId] == bytes32(0), "Right ID already exists");
        
        rightMetadataHashes[rightId] = metadataHash;
        rightsOwned[msg.sender].push(rightId);
        
        emit RightRegistered(rightId, msg.sender);
    }
    
    /**
     * @dev Verify a music right (can only be called by authorized verifiers)
     * @param rightId Unique identifier for the right to verify
     */
    function verifyRight(bytes32 rightId) external onlyVerifier {
        require(rightMetadataHashes[rightId] != bytes32(0), "Right does not exist");
        require(!rightsVerified[rightId], "Right already verified");
        
        rightsVerified[rightId] = true;
        
        emit RightVerified(rightId, msg.sender);
    }
    
    /**
     * @dev Check if a right is verified
     * @param rightId Unique identifier for the right
     * @return True if the right is verified, false otherwise
     */
    function isRightVerified(bytes32 rightId) external view returns (bool) {
        require(rightMetadataHashes[rightId] != bytes32(0), "Right does not exist");
        return rightsVerified[rightId];
    }
    
    /**
     * @dev Get the metadata hash of a right
     * @param rightId Unique identifier for the right
     * @return Metadata hash associated with the right
     */
    function getRightMetadataHash(bytes32 rightId) external view returns (bytes32) {
        require(rightMetadataHashes[rightId] != bytes32(0), "Right does not exist");
        return rightMetadataHashes[rightId];
    }
    
    /**
     * @dev Transfer ownership of a right to another address
     * @param rightId Unique identifier for the right
     * @param to Address to transfer the right to
     */
    function transferRight(bytes32 rightId, address to) external {
        require(to != address(0), "Cannot transfer to zero address");
        
        // Verify the sender owns the right
        bool ownerFound = false;
        uint256 rightIndex = 0;
        
        bytes32[] storage senderRights = rightsOwned[msg.sender];
        for (uint i = 0; i < senderRights.length; i++) {
            if (senderRights[i] == rightId) {
                ownerFound = true;
                rightIndex = i;
                break;
            }
        }
        
        require(ownerFound, "Sender does not own this right");
        
        // Remove the right from the sender
        if (rightIndex < senderRights.length - 1) {
            senderRights[rightIndex] = senderRights[senderRights.length - 1];
        }
        senderRights.pop();
        
        // Add the right to the recipient
        rightsOwned[to].push(rightId);
        
        emit RightTransferred(rightId, msg.sender, to);
    }
    
    /**
     * @dev Get all rights owned by the caller
     * @return Array of right IDs owned by the caller
     */
    function getMyRights() external view returns (bytes32[] memory) {
        return rightsOwned[msg.sender];
    }
    
    /**
     * @dev Submit a zero-knowledge proof to verify ownership without revealing specific rights
     * @param proof The proof data (placeholder for actual ZK proof implementation)
     * @return Whether the proof is valid
     */
    function submitOwnershipProof(bytes calldata proof) external pure returns (bool) {
        // This is a placeholder for actual ZK proof verification
        // In a real implementation, this would verify a zero-knowledge proof
        // that demonstrates ownership of a right without revealing which specific right
        
        // The Base chain would be used for the verification while keeping the rights data private
        
        // For now, return true to simulate a valid proof
        require(proof.length > 0, "Proof cannot be empty");
        return true;
    }
} 