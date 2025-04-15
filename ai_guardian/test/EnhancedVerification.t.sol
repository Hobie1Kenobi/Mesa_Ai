// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../src/EnhancedVerification.sol";
import "../src/RightsVault.sol";

contract EnhancedVerificationTest is Test {
    EnhancedVerification public enhancedVerification;
    RightsVault public rightsVault;
    address public owner;
    address public verifier1;
    address public verifier2;
    address public verifier3;

    function setUp() public {
        owner = address(this);
        verifier1 = makeAddr("verifier1");
        verifier2 = makeAddr("verifier2");
        verifier3 = makeAddr("verifier3");

        // Deploy RightsVault first
        rightsVault = new RightsVault();
        
        // Deploy EnhancedVerification with RightsVault address
        enhancedVerification = new EnhancedVerification(address(rightsVault));
    }

    function testAddVerification() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");
        
        // First register rights in RightsVault
        rightsVault.registerRights(rightsId, encryptedData, dataHash);
        
        bytes32 verificationId = enhancedVerification.addVerification(
            rightsId,
            EnhancedVerification.VerificationType.Identity,
            "Test verification evidence"
        );

        EnhancedVerification.Verification memory verification = enhancedVerification.getVerification(verificationId);

        assertEq(verification.rightsId, rightsId);
        assertEq(uint(verification.vType), uint(EnhancedVerification.VerificationType.Identity));
        assertEq(verification.verifier, address(this));
        assertTrue(verification.isValid);
        assertEq(verification.evidence, "Test verification evidence");
    }

    function testCreateMultiSigVerification() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");
        
        // First register rights in RightsVault
        rightsVault.registerRights(rightsId, encryptedData, dataHash);
        
        address[] memory verifiers = new address[](3);
        verifiers[0] = verifier1;
        verifiers[1] = verifier2;
        verifiers[2] = verifier3;
        uint256 requiredSignatures = 2;

        bytes32 multiSigId = enhancedVerification.createMultiSigVerification(
            rightsId,
            verifiers,
            requiredSignatures
        );

        // Get the verifiers array from the contract
        address[] memory storedVerifiers = enhancedVerification.getMultiSigVerifiers(multiSigId);
        uint256 storedRequiredSignatures = enhancedVerification.getMultiSigRequiredSignatures(multiSigId);
        bool isComplete = enhancedVerification.isMultiSigComplete(multiSigId);

        assertEq(storedVerifiers.length, verifiers.length);
        for (uint i = 0; i < verifiers.length; i++) {
            assertEq(storedVerifiers[i], verifiers[i]);
        }
        assertEq(storedRequiredSignatures, requiredSignatures);
        assertFalse(isComplete);
    }

    function testSignMultiSigVerification() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");
        
        // First register rights in RightsVault
        rightsVault.registerRights(rightsId, encryptedData, dataHash);
        
        address[] memory verifiers = new address[](3);
        verifiers[0] = verifier1;
        verifiers[1] = verifier2;
        verifiers[2] = verifier3;
        uint256 requiredSignatures = 2;

        bytes32 multiSigId = enhancedVerification.createMultiSigVerification(
            rightsId,
            verifiers,
            requiredSignatures
        );

        vm.prank(verifier1);
        enhancedVerification.signMultiSigVerification(multiSigId);

        vm.prank(verifier2);
        enhancedVerification.signMultiSigVerification(multiSigId);

        assertTrue(enhancedVerification.isMultiSigComplete(multiSigId));
    }

    function testInvalidateVerification() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");
        
        // First register rights in RightsVault
        rightsVault.registerRights(rightsId, encryptedData, dataHash);
        
        bytes32 verificationId = enhancedVerification.addVerification(
            rightsId,
            EnhancedVerification.VerificationType.Ownership,
            "Test verification evidence"
        );

        enhancedVerification.invalidateVerification(verificationId);

        EnhancedVerification.Verification memory verification = enhancedVerification.getVerification(verificationId);
        assertFalse(verification.isValid);
    }

    function test_RevertWhen_InvalidatingAsNonVerifier() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");
        
        // First register rights in RightsVault
        rightsVault.registerRights(rightsId, encryptedData, dataHash);
        
        bytes32 verificationId = enhancedVerification.addVerification(
            rightsId,
            EnhancedVerification.VerificationType.Usage,
            "Test verification evidence"
        );

        vm.prank(verifier1);
        vm.expectRevert("Not verifier");
        enhancedVerification.invalidateVerification(verificationId);
    }

    function test_RevertWhen_SigningAsNonVerifier() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");
        
        // First register rights in RightsVault
        rightsVault.registerRights(rightsId, encryptedData, dataHash);
        
        address[] memory verifiers = new address[](2);
        verifiers[0] = verifier1;
        verifiers[1] = verifier2;
        uint256 requiredSignatures = 2;

        bytes32 multiSigId = enhancedVerification.createMultiSigVerification(
            rightsId,
            verifiers,
            requiredSignatures
        );

        vm.prank(verifier3);
        vm.expectRevert("Not a verifier");
        enhancedVerification.signMultiSigVerification(multiSigId);
    }

    function test_RevertWhen_SigningTwice() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");
        
        // First register rights in RightsVault
        rightsVault.registerRights(rightsId, encryptedData, dataHash);
        
        address[] memory verifiers = new address[](2);
        verifiers[0] = verifier1;
        verifiers[1] = verifier2;
        uint256 requiredSignatures = 2;

        bytes32 multiSigId = enhancedVerification.createMultiSigVerification(
            rightsId,
            verifiers,
            requiredSignatures
        );

        vm.startPrank(verifier1);
        enhancedVerification.signMultiSigVerification(multiSigId);
        vm.expectRevert("Already signed");
        enhancedVerification.signMultiSigVerification(multiSigId);
        vm.stopPrank();
    }
} 