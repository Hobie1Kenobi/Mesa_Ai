// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "./ERC6551Account.sol";

/**
 * @title MusicRightsContainer
 * @dev Token-bound container for music rights with attestation support
 */
contract MusicRightsContainer is ERC6551Account {
    // Payment splitting receivers and their shares
    address[] public recipients;
    uint256[] public shares;
    uint256 public totalShares;
    
    // Attestation data
    struct AttestationData {
        bytes32 attestationId;     // EAS attestation ID
        string contractId;         // Reference to traditional contract
        string rightsType;         // Type of rights (composition, recording, etc.)
        string territory;          // Territory covered
        uint256 timestamp;         // When attestation was added
    }
    
    AttestationData[] public attestations;
    
    // Mapping of rights holders by email (allows adding parties later)
    mapping(string => address) public rightsHolderWallets;
    
    // Events
    event AttestationAdded(bytes32 attestationId, string contractId);
    event PaymentSplitConfigured(address[] recipients, uint256[] shares);
    event PaymentDistributed(uint256 amount);
    event RightsHolderAdded(string email, address wallet);
    
    /**
     * @dev Function to check whether a signer is valid
     * @param signer The address to check
     * @return Magic value if the signer is valid
     */
    function isValidSigner(address signer, bytes calldata) external view returns (bytes4) {
        (, address tokenContract, uint256 tokenId) = _token();
        
        // Check if signer is owner of the NFT
        // Simplified for demo - in production, we would check NFT ownership
        
        return IERC6551Account.isValidSigner.selector;
    }
    
    /**
     * @dev Initialize the container with attestation data
     * @param attestationId EAS attestation ID
     * @param contractId Traditional contract reference
     * @param rightsType Type of rights
     * @param territory Territory covered
     */
    function initialize(
        bytes32 attestationId,
        string calldata contractId,
        string calldata rightsType,
        string calldata territory
    ) external {
        // Only owner can initialize
        (, address tokenContract, uint256 tokenId) = _token();
        
        // Add attestation
        attestations.push(AttestationData({
            attestationId: attestationId,
            contractId: contractId,
            rightsType: rightsType,
            territory: territory,
            timestamp: block.timestamp
        }));
        
        emit AttestationAdded(attestationId, contractId);
    }
    
    /**
     * @dev Add a new attestation to the container
     * @param attestationId EAS attestation ID
     * @param contractId Traditional contract reference
     * @param rightsType Type of rights
     * @param territory Territory covered
     */
    function addAttestation(
        bytes32 attestationId,
        string calldata contractId,
        string calldata rightsType,
        string calldata territory
    ) external {
        // Only owner can add attestations
        (, address tokenContract, uint256 tokenId) = _token();
        
        attestations.push(AttestationData({
            attestationId: attestationId,
            contractId: contractId,
            rightsType: rightsType,
            territory: territory,
            timestamp: block.timestamp
        }));
        
        emit AttestationAdded(attestationId, contractId);
    }
    
    /**
     * @dev Configure payment splitting
     * @param _recipients Array of recipient addresses
     * @param _shares Array of shares for each recipient
     */
    function configurePaymentSplitting(
        address[] calldata _recipients,
        uint256[] calldata _shares
    ) external {
        // Only owner can configure payment splitting
        (, address tokenContract, uint256 tokenId) = _token();
        
        require(_recipients.length == _shares.length, "Arrays length mismatch");
        require(_recipients.length > 0, "Empty arrays");
        
        // Clear existing configuration
        delete recipients;
        delete shares;
        
        uint256 _totalShares = 0;
        
        // Set new configuration
        for (uint256 i = 0; i < _recipients.length; i++) {
            recipients.push(_recipients[i]);
            shares.push(_shares[i]);
            _totalShares += _shares[i];
        }
        
        totalShares = _totalShares;
        
        emit PaymentSplitConfigured(_recipients, _shares);
    }
    
    /**
     * @dev Add a rights holder wallet by email
     * @param email Email of the rights holder
     * @param wallet Wallet address
     */
    function addRightsHolderWallet(string calldata email, address wallet) external {
        // Only owner can add rights holders
        (, address tokenContract, uint256 tokenId) = _token();
        
        require(wallet != address(0), "Invalid wallet address");
        require(bytes(email).length > 0, "Invalid email");
        
        rightsHolderWallets[email] = wallet;
        
        emit RightsHolderAdded(email, wallet);
    }
    
    /**
     * @dev Distribute payment to all recipients
     */
    function distributePayment() external payable {
        require(totalShares > 0, "No payment splitting configured");
        
        uint256 amount = address(this).balance;
        
        for (uint256 i = 0; i < recipients.length; i++) {
            uint256 payment = (amount * shares[i]) / totalShares;
            
            if (payment > 0) {
                (bool success, ) = recipients[i].call{value: payment}("");
                require(success, "Payment failed");
            }
        }
        
        emit PaymentDistributed(amount);
    }
    
    /**
     * @dev Get all attestations
     * @return Array of attestation data
     */
    function getAttestations() external view returns (AttestationData[] memory) {
        return attestations;
    }
    
    /**
     * @dev Get payment splitting configuration
     * @return _recipients Array of recipient addresses
     * @return _shares Array of shares for each recipient
     */
    function getPaymentSplittingConfig() external view returns (
        address[] memory _recipients,
        uint256[] memory _shares
    ) {
        return (recipients, shares);
    }
} 