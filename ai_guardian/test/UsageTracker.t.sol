// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../src/UsageTracker.sol";
import "../src/RightsVault.sol";

contract UsageTrackerTest is Test {
    UsageTracker public usageTracker;
    RightsVault public rightsVault;
    address public owner;
    address public licensee;
    address public user;

    function setUp() public {
        owner = address(this);
        licensee = makeAddr("licensee");
        user = makeAddr("user");

        // Deploy RightsVault first
        rightsVault = new RightsVault();
        
        // Deploy UsageTracker with RightsVault address
        usageTracker = new UsageTracker(address(rightsVault));

        // Fund accounts for testing
        vm.deal(licensee, 10 ether);
        vm.deal(user, 10 ether);
    }

    function testCreateLicense() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 licenseId = usageTracker.createLicense(
            rightsId,
            licensee,
            UsageTracker.LicenseType.Commercial,
            block.timestamp,
            block.timestamp + 1 days,
            100,
            1 ether
        );

        UsageTracker.License memory license = usageTracker.getLicenseData(licenseId);

        assertEq(license.rightsId, rightsId);
        assertEq(license.licensee, licensee);
        assertEq(uint(license.lType), uint(UsageTracker.LicenseType.Commercial));
        assertEq(license.startTime, block.timestamp);
        assertEq(license.endTime, block.timestamp + 1 days);
        assertEq(license.maxUses, 100);
        assertEq(license.currentUses, 0);
        assertTrue(license.isActive);
        assertEq(license.fee, 1 ether);
    }

    function testRecordUsage() public {
        bytes32 rightsId = keccak256("testRights");
        
        vm.prank(user);
        bytes32 usageId = usageTracker.recordUsage(
            rightsId,
            UsageTracker.UsageType.Streaming,
            "testMetadata"
        );

        UsageTracker.UsageRecord memory record = usageTracker.getUsageRecord(usageId);

        assertEq(record.rightsId, rightsId);
        assertEq(record.user, user);
        assertEq(uint(record.uType), uint(UsageTracker.UsageType.Streaming));
        assertEq(record.metadata, "testMetadata");
    }

    function testUpdateLicense() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 licenseId = usageTracker.createLicense(
            rightsId,
            licensee,
            UsageTracker.LicenseType.Commercial,
            block.timestamp,
            block.timestamp + 1 days,
            100,
            1 ether
        );

        uint256 newEndTime = block.timestamp + 2 days;
        uint256 newMaxUses = 200;
        uint256 newFee = 2 ether;

        usageTracker.updateLicense(licenseId, newEndTime, newMaxUses, newFee);

        UsageTracker.License memory license = usageTracker.getLicenseData(licenseId);

        assertEq(license.endTime, newEndTime);
        assertEq(license.maxUses, newMaxUses);
        assertEq(license.fee, newFee);
    }

    function testRevokeLicense() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 licenseId = usageTracker.createLicense(
            rightsId,
            licensee,
            UsageTracker.LicenseType.Commercial,
            block.timestamp,
            block.timestamp + 1 days,
            100,
            1 ether
        );

        usageTracker.revokeLicense(licenseId);

        UsageTracker.License memory license = usageTracker.getLicenseData(licenseId);
        assertFalse(license.isActive);
    }

    function testGetRightsLicenses() public {
        bytes32 rightsId = keccak256("testRights");
        
        // Create multiple licenses for the same rights
        bytes32 licenseId1 = usageTracker.createLicense(
            rightsId,
            licensee,
            UsageTracker.LicenseType.Commercial,
            block.timestamp,
            block.timestamp + 1 days,
            100,
            1 ether
        );

        bytes32 licenseId2 = usageTracker.createLicense(
            rightsId,
            licensee,
            UsageTracker.LicenseType.NonCommercial,
            block.timestamp,
            block.timestamp + 2 days,
            50,
            0.5 ether
        );

        bytes32[] memory licenses = usageTracker.getRightsLicenses(rightsId);
        assertEq(licenses.length, 2);
        assertEq(licenses[0], licenseId1);
        assertEq(licenses[1], licenseId2);
    }

    function testGetRightsUsageRecords() public {
        bytes32 rightsId = keccak256("testRights");
        
        // Record multiple usages
        bytes32 usageId1 = usageTracker.recordUsage(
            rightsId,
            UsageTracker.UsageType.Streaming,
            "metadata1"
        );

        bytes32 usageId2 = usageTracker.recordUsage(
            rightsId,
            UsageTracker.UsageType.Download,
            "metadata2"
        );

        bytes32[] memory records = usageTracker.getRightsUsageRecords(rightsId);
        assertEq(records.length, 2);
        assertEq(records[0], usageId1);
        assertEq(records[1], usageId2);
    }

    function testIsLicenseValid() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 licenseId = usageTracker.createLicense(
            rightsId,
            licensee,
            UsageTracker.LicenseType.Commercial,
            block.timestamp,
            block.timestamp + 1 days,
            100,
            1 ether
        );

        assertTrue(usageTracker.isLicenseValid(licenseId));

        // Test expired license
        vm.warp(block.timestamp + 2 days);
        assertFalse(usageTracker.isLicenseValid(licenseId));
    }

    function test_RevertWhen_UpdatingWithInvalidEndTime() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 licenseId = usageTracker.createLicense(
            rightsId,
            licensee,
            UsageTracker.LicenseType.Commercial,
            block.timestamp,
            block.timestamp + 1 days,
            100,
            1 ether
        );

        // Try to update with invalid end time
        vm.expectRevert("Invalid end time");
        usageTracker.updateLicense(licenseId, block.timestamp - 1, 100, 1 ether);
    }

    function test_RevertWhen_RevokingInactiveLicense() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 licenseId = usageTracker.createLicense(
            rightsId,
            licensee,
            UsageTracker.LicenseType.Commercial,
            block.timestamp,
            block.timestamp + 1 days,
            100,
            1 ether
        );

        usageTracker.revokeLicense(licenseId);

        vm.expectRevert("License not active");
        usageTracker.revokeLicense(licenseId);
    }
} 