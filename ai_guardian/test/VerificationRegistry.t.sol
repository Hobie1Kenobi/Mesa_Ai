// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../src/VerificationRegistry.sol";

contract VerificationRegistryTest is Test {
    VerificationRegistry public registry;
    address public owner;
    address public verifier;

    function setUp() public {
        owner = address(this);
        verifier = makeAddr("verifier");

        // Deploy VerificationRegistry
        registry = new VerificationRegistry();
    }

    function testRegisterVerification() public {
        bytes32 verificationId = keccak256("testVerification");
        bytes32 rightsId = keccak256("testRights");
        bytes32 proofHash = keccak256("testProof");

        registry.registerVerification(verificationId, rightsId, proofHash);

        VerificationRegistry.VerificationData memory data = registry.getVerificationData(verificationId);
        assertEq(data.rightsId, rightsId);
        assertEq(data.proofHash, proofHash);
        assertEq(data.verifier, address(this));
        assertEq(data.timestamp, block.timestamp);
        assertTrue(data.isValid);

        bytes32[] memory verifications = registry.getRightsVerifications(rightsId);
        assertEq(verifications.length, 1);
        assertEq(verifications[0], verificationId);
    }

    function testInvalidateVerification() public {
        bytes32 verificationId = keccak256("testVerification");
        bytes32 rightsId = keccak256("testRights");
        bytes32 proofHash = keccak256("testProof");

        registry.registerVerification(verificationId, rightsId, proofHash);
        registry.invalidateVerification(verificationId);

        VerificationRegistry.VerificationData memory data = registry.getVerificationData(verificationId);
        assertFalse(data.isValid);
    }

    function testHasValidVerifications() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 proofHash = keccak256("testProof");

        bytes32 verificationId1 = keccak256("testVerification1");
        bytes32 verificationId2 = keccak256("testVerification2");

        registry.registerVerification(verificationId1, rightsId, proofHash);
        registry.registerVerification(verificationId2, rightsId, proofHash);

        assertTrue(registry.hasValidVerifications(rightsId));

        registry.invalidateVerification(verificationId1);
        assertTrue(registry.hasValidVerifications(rightsId));

        registry.invalidateVerification(verificationId2);
        assertFalse(registry.hasValidVerifications(rightsId));
    }

    function test_RevertWhen_RegisteringDuplicateVerification() public {
        bytes32 verificationId = keccak256("testVerification");
        bytes32 rightsId = keccak256("testRights");
        bytes32 proofHash = keccak256("testProof");

        registry.registerVerification(verificationId, rightsId, proofHash);

        vm.expectRevert("Verification already exists");
        registry.registerVerification(verificationId, rightsId, proofHash);
    }

    function test_RevertWhen_InvalidatingAsNonVerifier() public {
        bytes32 verificationId = keccak256("testVerification");
        bytes32 rightsId = keccak256("testRights");
        bytes32 proofHash = keccak256("testProof");

        registry.registerVerification(verificationId, rightsId, proofHash);

        vm.prank(verifier);
        vm.expectRevert("Not verifier");
        registry.invalidateVerification(verificationId);
    }

    function test_RevertWhen_InvalidatingInvalidVerification() public {
        bytes32 verificationId = keccak256("testVerification");
        bytes32 rightsId = keccak256("testRights");
        bytes32 proofHash = keccak256("testProof");

        registry.registerVerification(verificationId, rightsId, proofHash);
        registry.invalidateVerification(verificationId);

        vm.expectRevert("Already invalid");
        registry.invalidateVerification(verificationId);
    }
} 