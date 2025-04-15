// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title VerificationRegistry
 * @dev Contract for managing rights verification status and ZK proofs
 */
contract VerificationRegistry {
    address public owner;
    bool private locked;

    // Struct to store verification data
    struct VerificationData {
        bytes32 rightsId;           // ID of the rights being verified
        bytes32 proofHash;          // Hash of the ZK proof
        address verifier;           // Address of the verifier
        uint256 timestamp;          // Timestamp of verification
        bool isValid;               // Whether the verification is valid
    }

    // Mapping from verification ID to VerificationData
    mapping(bytes32 => VerificationData) public verifications;
    
    // Mapping from rights ID to array of verification IDs
    mapping(bytes32 => bytes32[]) public rightsVerifications;
    
    // Events
    event VerificationRegistered(
        bytes32 indexed verificationId,
        bytes32 indexed rightsId,
        address indexed verifier
    );
    event VerificationInvalidated(bytes32 indexed verificationId);

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
     * @dev Register a new verification
     * @param verificationId Unique identifier for the verification
     * @param rightsId ID of the rights being verified
     * @param proofHash Hash of the ZK proof
     */
    function registerVerification(
        bytes32 verificationId,
        bytes32 rightsId,
        bytes32 proofHash
    ) external nonReentrant {
        require(verifications[verificationId].timestamp == 0, "Verification already exists");
        
        verifications[verificationId] = VerificationData({
            rightsId: rightsId,
            proofHash: proofHash,
            verifier: msg.sender,
            timestamp: block.timestamp,
            isValid: true
        });
        
        rightsVerifications[rightsId].push(verificationId);
        
        emit VerificationRegistered(verificationId, rightsId, msg.sender);
    }

    /**
     * @dev Invalidate a verification
     * @param verificationId ID of the verification to invalidate
     */
    function invalidateVerification(bytes32 verificationId) external nonReentrant {
        require(verifications[verificationId].verifier == msg.sender, "Not verifier");
        require(verifications[verificationId].isValid, "Already invalid");
        
        verifications[verificationId].isValid = false;
        
        emit VerificationInvalidated(verificationId);
    }

    /**
     * @dev Get verification data
     * @param verificationId Verification identifier
     * @return VerificationData struct containing the verification information
     */
    function getVerificationData(bytes32 verificationId) external view returns (VerificationData memory) {
        return verifications[verificationId];
    }

    /**
     * @dev Get all verifications for specific rights
     * @param rightsId Rights identifier
     * @return Array of verification IDs
     */
    function getRightsVerifications(bytes32 rightsId) external view returns (bytes32[] memory) {
        return rightsVerifications[rightsId];
    }

    /**
     * @dev Check if rights have valid verifications
     * @param rightsId Rights identifier
     * @return bool indicating if valid verifications exist
     */
    function hasValidVerifications(bytes32 rightsId) external view returns (bool) {
        bytes32[] memory verificationIds = rightsVerifications[rightsId];
        for (uint i = 0; i < verificationIds.length; i++) {
            if (verifications[verificationIds[i]].isValid) {
                return true;
            }
        }
        return false;
    }
} 