// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title VerificationRegistry
 * @dev A contract for managing verifications related to music rights
 * This contract allows authorized verifiers to issue verifications for music rights,
 * which can be used to prove authenticity without revealing sensitive details.
 */
contract VerificationRegistry {
    // Struct for verification data
    struct Verification {
        address issuer;        // Address of the verifier who issued this verification
        string claim;          // The claim being verified (e.g., "original composer", "published work")
        bytes32 rightId;       // ID of the right being verified
        uint256 issuedAt;      // Timestamp when the verification was issued
        uint256 expiresAt;     // Timestamp when the verification expires (0 for no expiration)
        bytes signature;       // Signature from the verifier
        bool revoked;          // Whether the verification has been revoked
    }
    
    // Owner of the contract
    address public owner;
    
    // Mapping of verification IDs to verification data
    mapping(bytes32 => Verification) private verifications;
    
    // Mapping of subject (right owner) to their verification IDs
    mapping(address => bytes32[]) private subjectVerifications;
    
    // Mapping of authorized verifiers
    mapping(address => bool) public authorizedVerifiers;
    
    // Events
    event VerificationIssued(bytes32 indexed verificationId, address indexed issuer, address indexed subject, bytes32 rightId);
    event VerificationRevoked(bytes32 indexed verificationId, address indexed revoker);
    event VerifierAdded(address indexed verifier);
    event VerifierRemoved(address indexed verifier);
    
    /**
     * @dev Constructor that sets the contract owner
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
        require(!authorizedVerifiers[verifier], "Address is already a verifier");
        
        authorizedVerifiers[verifier] = true;
        
        emit VerifierAdded(verifier);
    }
    
    /**
     * @dev Remove a verifier from the authorized list
     * @param verifier Address of the verifier to remove
     */
    function removeVerifier(address verifier) external onlyOwner {
        require(authorizedVerifiers[verifier], "Address is not a verifier");
        
        authorizedVerifiers[verifier] = false;
        
        emit VerifierRemoved(verifier);
    }
    
    /**
     * @dev Issue a verification for a music right
     * @param subject Address of the right owner
     * @param rightId ID of the right being verified
     * @param claim The claim being verified
     * @param expiresAt Timestamp when the verification expires (0 for no expiration)
     * @param signature Signature from the verifier
     * @return verificationId The unique ID of the verification
     */
    function issueVerification(
        address subject,
        bytes32 rightId,
        string calldata claim,
        uint256 expiresAt,
        bytes calldata signature
    ) external onlyVerifier returns (bytes32) {
        require(subject != address(0), "Invalid subject address");
        
        // Create a unique verification ID
        bytes32 verificationId = keccak256(
            abi.encodePacked(
                msg.sender,
                subject,
                rightId,
                claim,
                block.timestamp
            )
        );
        
        // Ensure verification ID is unique
        require(verifications[verificationId].issuer == address(0), "Verification ID already exists");
        
        // Create and store the verification
        Verification memory verification = Verification({
            issuer: msg.sender,
            claim: claim,
            rightId: rightId,
            issuedAt: block.timestamp,
            expiresAt: expiresAt,
            signature: signature,
            revoked: false
        });
        
        verifications[verificationId] = verification;
        subjectVerifications[subject].push(verificationId);
        
        emit VerificationIssued(verificationId, msg.sender, subject, rightId);
        
        return verificationId;
    }
    
    /**
     * @dev Revoke a verification
     * @param verificationId ID of the verification to revoke
     */
    function revokeVerification(bytes32 verificationId) external {
        Verification storage verification = verifications[verificationId];
        
        // Only the issuer or the contract owner can revoke
        require(
            verification.issuer == msg.sender || msg.sender == owner,
            "Only the issuer or contract owner can revoke"
        );
        
        // Ensure the verification exists and is not already revoked
        require(verification.issuer != address(0), "Verification does not exist");
        require(!verification.revoked, "Verification is already revoked");
        
        verification.revoked = true;
        
        emit VerificationRevoked(verificationId, msg.sender);
    }
    
    /**
     * @dev Check if a verification is valid
     * @param verificationId ID of the verification to check
     * @return True if the verification is valid (not expired and not revoked)
     */
    function isVerificationValid(bytes32 verificationId) external view returns (bool) {
        Verification memory verification = verifications[verificationId];
        
        // Check if the verification exists
        if (verification.issuer == address(0)) {
            return false;
        }
        
        // Check if the verification is revoked
        if (verification.revoked) {
            return false;
        }
        
        // Check if the verification is expired
        if (verification.expiresAt > 0 && verification.expiresAt < block.timestamp) {
            return false;
        }
        
        // Check if the issuer is still an authorized verifier
        if (!authorizedVerifiers[verification.issuer]) {
            return false;
        }
        
        return true;
    }
    
    /**
     * @dev Get all verification IDs for a subject
     * @param subject Address of the subject
     * @return Array of verification IDs
     */
    function getVerificationIds(address subject) external view returns (bytes32[] memory) {
        return subjectVerifications[subject];
    }
    
    /**
     * @dev Get verification details
     * @param verificationId ID of the verification
     * @return The verification details
     */
    function getVerification(bytes32 verificationId) external view returns (
        address issuer,
        string memory claim,
        bytes32 rightId,
        uint256 issuedAt,
        uint256 expiresAt,
        bool revoked
    ) {
        Verification memory verification = verifications[verificationId];
        
        require(verification.issuer != address(0), "Verification does not exist");
        
        return (
            verification.issuer,
            verification.claim,
            verification.rightId,
            verification.issuedAt,
            verification.expiresAt,
            verification.revoked
        );
    }
    
    /**
     * @dev Transfer ownership of the contract to a new address
     * @param newOwner Address of the new owner
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid owner address");
        owner = newOwner;
    }
} 