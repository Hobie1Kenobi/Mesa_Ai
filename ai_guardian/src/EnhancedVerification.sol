// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./RightsVault.sol";

/**
 * @title EnhancedVerification
 * @dev Enhanced verification system for rights management
 */
contract EnhancedVerification {
    RightsVault public rightsVault;
    address public owner;
    bool private locked;

    // Verification types
    enum VerificationType { Identity, Ownership, Usage, License }

    // Struct for verification data
    struct Verification {
        bytes32 rightsId;
        VerificationType vType;
        address verifier;
        uint256 timestamp;
        bool isValid;
        string evidence;
    }

    // Struct for multi-signature verification
    struct MultiSigVerification {
        bytes32 rightsId;
        address[] verifiers;
        uint256 requiredSignatures;
        mapping(address => bool) hasSigned;
        uint256 signatureCount;
        bool isComplete;
    }

    // Mapping from verification ID to Verification
    mapping(bytes32 => Verification) public verifications;
    
    // Mapping from rights ID to array of verification IDs
    mapping(bytes32 => bytes32[]) public rightsVerifications;
    
    // Mapping from multi-sig ID to MultiSigVerification
    mapping(bytes32 => MultiSigVerification) public multiSigVerifications;
    
    // Events
    event VerificationAdded(
        bytes32 indexed verificationId,
        bytes32 indexed rightsId,
        VerificationType vType,
        address indexed verifier
    );
    event VerificationInvalidated(bytes32 indexed verificationId);
    event MultiSigVerificationCreated(
        bytes32 indexed multiSigId,
        bytes32 indexed rightsId,
        uint256 requiredSignatures
    );
    event MultiSigVerificationSigned(
        bytes32 indexed multiSigId,
        address indexed signer
    );
    event MultiSigVerificationCompleted(bytes32 indexed multiSigId);

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
     * @dev Add a new verification
     * @param rightsId Rights identifier
     * @param vType Type of verification
     * @param evidence Verification evidence
     * @return verificationId Unique identifier for the verification
     */
    function addVerification(
        bytes32 rightsId,
        VerificationType vType,
        string calldata evidence
    ) external nonReentrant returns (bytes32) {
        bytes32 verificationId = keccak256(
            abi.encodePacked(
                rightsId,
                vType,
                msg.sender,
                block.timestamp,
                evidence
            )
        );

        verifications[verificationId] = Verification({
            rightsId: rightsId,
            vType: vType,
            verifier: msg.sender,
            timestamp: block.timestamp,
            isValid: true,
            evidence: evidence
        });

        rightsVerifications[rightsId].push(verificationId);

        emit VerificationAdded(verificationId, rightsId, vType, msg.sender);
        return verificationId;
    }

    /**
     * @dev Create a new multi-signature verification
     * @param rightsId Rights identifier
     * @param verifiers Array of verifier addresses
     * @param requiredSignatures Number of required signatures
     * @return multiSigId Unique identifier for the multi-sig verification
     */
    function createMultiSigVerification(
        bytes32 rightsId,
        address[] calldata verifiers,
        uint256 requiredSignatures
    ) external nonReentrant returns (bytes32) {
        require(requiredSignatures > 0 && requiredSignatures <= verifiers.length, "Invalid required signatures");
        
        bytes32 multiSigId = keccak256(
            abi.encodePacked(
                rightsId,
                verifiers,
                requiredSignatures,
                block.timestamp
            )
        );

        MultiSigVerification storage multiSig = multiSigVerifications[multiSigId];
        multiSig.rightsId = rightsId;
        multiSig.verifiers = verifiers;
        multiSig.requiredSignatures = requiredSignatures;
        multiSig.signatureCount = 0;
        multiSig.isComplete = false;

        emit MultiSigVerificationCreated(multiSigId, rightsId, requiredSignatures);
        return multiSigId;
    }

    /**
     * @dev Sign a multi-signature verification
     * @param multiSigId Multi-signature verification identifier
     */
    function signMultiSigVerification(bytes32 multiSigId) external nonReentrant {
        MultiSigVerification storage multiSig = multiSigVerifications[multiSigId];
        require(!multiSig.isComplete, "Verification already complete");
        require(!multiSig.hasSigned[msg.sender], "Already signed");
        
        bool isVerifier = false;
        for (uint i = 0; i < multiSig.verifiers.length; i++) {
            if (multiSig.verifiers[i] == msg.sender) {
                isVerifier = true;
                break;
            }
        }
        require(isVerifier, "Not a verifier");

        multiSig.hasSigned[msg.sender] = true;
        multiSig.signatureCount++;

        emit MultiSigVerificationSigned(multiSigId, msg.sender);

        if (multiSig.signatureCount >= multiSig.requiredSignatures) {
            multiSig.isComplete = true;
            emit MultiSigVerificationCompleted(multiSigId);
        }
    }

    /**
     * @dev Invalidate a verification
     * @param verificationId Verification identifier
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
     * @return Verification struct containing the verification information
     */
    function getVerification(bytes32 verificationId) external view returns (Verification memory) {
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
     * @dev Get multi-signature verification data
     * @param multiSigId Multi-signature verification identifier
     * @return rightsId Rights identifier
     * @return verifiers Array of verifier addresses
     * @return requiredSignatures Number of required signatures
     * @return signatureCount Current number of signatures
     * @return isComplete Whether the verification is complete
     */
    function getMultiSigVerificationData(bytes32 multiSigId) external view returns (
        bytes32 rightsId,
        address[] memory verifiers,
        uint256 requiredSignatures,
        uint256 signatureCount,
        bool isComplete
    ) {
        MultiSigVerification storage multiSig = multiSigVerifications[multiSigId];
        return (
            multiSig.rightsId,
            multiSig.verifiers,
            multiSig.requiredSignatures,
            multiSig.signatureCount,
            multiSig.isComplete
        );
    }

    /**
     * @dev Get verifiers for a multi-signature verification
     * @param multiSigId Multi-signature verification identifier
     * @return Array of verifier addresses
     */
    function getMultiSigVerifiers(bytes32 multiSigId) external view returns (address[] memory) {
        return multiSigVerifications[multiSigId].verifiers;
    }

    /**
     * @dev Get required signatures for a multi-signature verification
     * @param multiSigId Multi-signature verification identifier
     * @return Number of required signatures
     */
    function getMultiSigRequiredSignatures(bytes32 multiSigId) external view returns (uint256) {
        return multiSigVerifications[multiSigId].requiredSignatures;
    }

    /**
     * @dev Check if a multi-signature verification is complete
     * @param multiSigId Multi-signature verification identifier
     * @return Whether the verification is complete
     */
    function isMultiSigComplete(bytes32 multiSigId) external view returns (bool) {
        return multiSigVerifications[multiSigId].isComplete;
    }
} 