// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../src/MusicRightsVault.sol";

contract MusicRightsVaultTest is Test {
    MusicRightsVault public musicRightsVault;
    address public owner;
    address public user;

    function setUp() public {
        owner = makeAddr("owner");
        user = makeAddr("user");

        // Deploy MusicRightsVault
        vm.prank(owner);
        musicRightsVault = new MusicRightsVault();
    }

    function testRegisterMusicRights() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");

        string[] memory rightsTypes = new string[](2);
        rightsTypes[0] = "mechanical";
        rightsTypes[1] = "performance";

        MusicRightsVault.MusicMetadata memory metadata = MusicRightsVault.MusicMetadata({
            mesaTrackId: "test-mesa-id",
            title: "Test Song",
            artist: "Test Artist",
            releaseYear: 2024,
            rightsTypes: rightsTypes
        });

        vm.prank(user);
        musicRightsVault.registerMusicRights(
            rightsId,
            encryptedData,
            dataHash,
            metadata
        );

        MusicRightsVault.MusicMetadata memory storedMetadata = musicRightsVault.getMusicMetadata(rightsId);
        RightsVault.RightsData memory rightsData = musicRightsVault.getRightsData(rightsId);

        assertEq(storedMetadata.mesaTrackId, "test-mesa-id");
        assertEq(storedMetadata.title, "Test Song");
        assertEq(storedMetadata.artist, "Test Artist");
        assertEq(storedMetadata.releaseYear, 2024);
        assertEq(storedMetadata.rightsTypes.length, 2);
        assertEq(storedMetadata.rightsTypes[0], "mechanical");
        assertEq(storedMetadata.rightsTypes[1], "performance");

        assertEq(rightsData.encryptedData, encryptedData);
        assertEq(rightsData.dataHash, dataHash);
        assertEq(rightsData.rightsOwner, user);
        assertTrue(rightsData.isActive);
    }

    function testHasRightsForMesaTrackId() public {
        bytes32 rightsId = keccak256("test-rights");
        bytes32 encryptedData = keccak256("test-data");
        bytes32 dataHash = keccak256("test-hash");
        
        MusicRightsVault.MusicMetadata memory metadata = MusicRightsVault.MusicMetadata({
            mesaTrackId: "test-mesa-id",
            title: "Test Song",
            artist: "Test Artist",
            releaseYear: 2024,
            rightsTypes: new string[](2)
        });

        vm.prank(user);
        musicRightsVault.registerMusicRights(
            rightsId,
            encryptedData,
            dataHash,
            metadata
        );

        vm.prank(user);
        assertTrue(musicRightsVault.hasRightsForMesaTrackId("test-mesa-id"));
        assertFalse(musicRightsVault.hasRightsForMesaTrackId("non-existent-mesa-id"));
    }

    function test_RevertWhen_RegisteringDuplicateRights() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");

        string[] memory rightsTypes = new string[](1);
        rightsTypes[0] = "mechanical";

        MusicRightsVault.MusicMetadata memory metadata = MusicRightsVault.MusicMetadata({
            mesaTrackId: "test-mesa-id",
            title: "Test Song",
            artist: "Test Artist",
            releaseYear: 2024,
            rightsTypes: rightsTypes
        });

        vm.prank(user);
        musicRightsVault.registerMusicRights(
            rightsId,
            encryptedData,
            dataHash,
            metadata
        );

        vm.prank(user);
        vm.expectRevert("Rights already registered");
        musicRightsVault.registerMusicRights(
            rightsId,
            encryptedData,
            dataHash,
            metadata
        );
    }
} 