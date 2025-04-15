// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../src/RightsVault.sol";

contract RightsVaultTest is Test {
    RightsVault public rightsVault;
    address public owner;
    address public user;

    function setUp() public {
        owner = address(this);
        user = address(0x1);
        rightsVault = new RightsVault();
    }

    function testRegisterRights() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");

        rightsVault.registerRights(rightsId, encryptedData, dataHash);

        RightsVault.RightsData memory data = rightsVault.getRightsData(rightsId);
        assertEq(data.encryptedData, encryptedData);
        assertEq(data.dataHash, dataHash);
        assertEq(data.rightsOwner, owner);
        assertTrue(data.isActive);
    }

    function testUpdateRights() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");

        rightsVault.registerRights(rightsId, encryptedData, dataHash);

        bytes32 newEncryptedData = keccak256("newEncryptedData");
        bytes32 newDataHash = keccak256("newDataHash");

        rightsVault.updateRights(rightsId, newEncryptedData, newDataHash);

        RightsVault.RightsData memory data = rightsVault.getRightsData(rightsId);
        assertEq(data.encryptedData, newEncryptedData);
        assertEq(data.dataHash, newDataHash);
    }

    function testDeactivateRights() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");

        rightsVault.registerRights(rightsId, encryptedData, dataHash);

        rightsVault.deactivateRights(rightsId);

        RightsVault.RightsData memory data = rightsVault.getRightsData(rightsId);
        assertFalse(data.isActive);
    }

    function test_RevertWhen_RegisteringDuplicateRights() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");

        rightsVault.registerRights(rightsId, encryptedData, dataHash);
        
        vm.expectRevert("Rights already registered");
        rightsVault.registerRights(rightsId, encryptedData, dataHash);
    }

    function test_RevertWhen_UpdatingNonExistentRights() public {
        bytes32 rightsId = keccak256("nonExistentRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");

        vm.expectRevert("Not rights owner");
        rightsVault.updateRights(rightsId, encryptedData, dataHash);
    }

    function test_RevertWhen_DeactivatingNonExistentRights() public {
        bytes32 rightsId = keccak256("nonExistentRights");

        vm.expectRevert("Not rights owner");
        rightsVault.deactivateRights(rightsId);
    }

    function testFuzzRegisterRights(bytes32 rightsId, bytes32 encryptedData, bytes32 dataHash) public {
        rightsVault.registerRights(rightsId, encryptedData, dataHash);

        RightsVault.RightsData memory data = rightsVault.getRightsData(rightsId);
        assertEq(data.encryptedData, encryptedData);
        assertEq(data.dataHash, dataHash);
        assertEq(data.rightsOwner, owner);
        assertTrue(data.isActive);
    }
} 