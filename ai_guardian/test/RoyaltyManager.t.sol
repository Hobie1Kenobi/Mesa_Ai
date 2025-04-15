// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../src/RoyaltyManager.sol";
import "../src/RightsVault.sol";

contract RoyaltyManagerTest is Test {
    RoyaltyManager public royaltyManager;
    RightsVault public rightsVault;
    address public owner;
    address public rightsHolder;
    address public licensee;
    address public user;

    function setUp() public {
        owner = address(this);
        rightsHolder = makeAddr("rightsHolder");
        licensee = makeAddr("licensee");
        user = makeAddr("user");

        // Deploy RightsVault first
        rightsVault = new RightsVault();
        
        // Deploy RoyaltyManager with RightsVault address
        royaltyManager = new RoyaltyManager(address(rightsVault));

        // Fund accounts for testing
        vm.deal(rightsHolder, 10 ether);
        vm.deal(licensee, 10 ether);
        vm.deal(user, 10 ether);
    }

    function testAddRoyaltySplit() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");
        
        // First register rights in RightsVault
        rightsVault.registerRights(rightsId, encryptedData, dataHash);
        
        // Add royalty split
        royaltyManager.addRoyaltySplit(
            rightsId,
            payable(licensee),
            1000 // 10% royalty rate (1000 = 10.00%)
        );

        RoyaltyManager.RoyaltySplit[] memory splits = royaltyManager.getRoyaltySplits(rightsId);
        assertEq(splits.length, 1);
        assertEq(splits[0].recipient, licensee);
        assertEq(splits[0].sharePercentage, 1000);
        assertTrue(splits[0].isActive);
        
        uint256 totalShares = royaltyManager.getTotalShares(rightsId);
        assertEq(totalShares, 1000);
    }

    function testUpdateRoyaltySplit() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");
        
        // First register rights in RightsVault
        rightsVault.registerRights(rightsId, encryptedData, dataHash);
        
        // Add royalty split
        royaltyManager.addRoyaltySplit(
            rightsId,
            payable(licensee),
            1000 // 10% royalty rate
        );

        // Update royalty split
        uint256 newSharePercentage = 1500; // 15% royalty rate
        royaltyManager.updateRoyaltySplit(rightsId, 0, newSharePercentage);

        RoyaltyManager.RoyaltySplit[] memory splits = royaltyManager.getRoyaltySplits(rightsId);
        assertEq(splits[0].sharePercentage, newSharePercentage);
        
        uint256 totalShares = royaltyManager.getTotalShares(rightsId);
        assertEq(totalShares, newSharePercentage);
    }

    function testRemoveRoyaltySplit() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");
        
        // First register rights in RightsVault
        rightsVault.registerRights(rightsId, encryptedData, dataHash);
        
        // Add royalty split
        royaltyManager.addRoyaltySplit(
            rightsId,
            payable(licensee),
            1000 // 10% royalty rate
        );

        // Remove royalty split
        royaltyManager.removeRoyaltySplit(rightsId, 0);

        RoyaltyManager.RoyaltySplit[] memory splits = royaltyManager.getRoyaltySplits(rightsId);
        assertFalse(splits[0].isActive);
        
        uint256 totalShares = royaltyManager.getTotalShares(rightsId);
        assertEq(totalShares, 0);
    }

    function testDistributeRoyalties() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");
        
        // First register rights in RightsVault
        vm.prank(rightsHolder);
        rightsVault.registerRights(rightsId, encryptedData, dataHash);
        
        // Add royalty split
        vm.prank(rightsHolder);
        royaltyManager.addRoyaltySplit(
            rightsId,
            payable(licensee),
            1000 // 10% royalty rate
        );

        // Record initial balances
        uint256 initialLicenseeBalance = licensee.balance;
        uint256 initialSenderBalance = address(this).balance;
        
        // Distribute royalties
        uint256 royaltyAmount = 1 ether;
        royaltyManager.distributeRoyalties{value: royaltyAmount}(rightsId);

        // Check that licensee received the correct amount (10% of 1 ether = 0.1 ether)
        assertEq(licensee.balance, initialLicenseeBalance + 0.1 ether);
        
        // Check that the remaining amount was refunded
        assertEq(address(this).balance, initialSenderBalance - royaltyAmount + (royaltyAmount * 9000 / 10000));
    }

    function testGetRoyaltySplits() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");
        
        // First register rights in RightsVault
        rightsVault.registerRights(rightsId, encryptedData, dataHash);
        
        // Add multiple royalty splits
        royaltyManager.addRoyaltySplit(
            rightsId,
            payable(licensee),
            1000 // 10% royalty rate
        );

        royaltyManager.addRoyaltySplit(
            rightsId,
            payable(user),
            2000 // 20% royalty rate
        );

        RoyaltyManager.RoyaltySplit[] memory splits = royaltyManager.getRoyaltySplits(rightsId);
        assertEq(splits.length, 2);
        assertEq(splits[0].recipient, licensee);
        assertEq(splits[0].sharePercentage, 1000);
        assertEq(splits[1].recipient, user);
        assertEq(splits[1].sharePercentage, 2000);
    }

    function testGetTotalShares() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");
        
        // First register rights in RightsVault
        rightsVault.registerRights(rightsId, encryptedData, dataHash);
        
        // Add royalty splits
        royaltyManager.addRoyaltySplit(
            rightsId,
            payable(licensee),
            1000 // 10% royalty rate
        );

        royaltyManager.addRoyaltySplit(
            rightsId,
            payable(user),
            2000 // 20% royalty rate
        );

        uint256 totalShares = royaltyManager.getTotalShares(rightsId);
        assertEq(totalShares, 3000); // 30% total
    }

    function test_RevertWhen_AddingInvalidSharePercentage() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");
        
        // First register rights in RightsVault
        rightsVault.registerRights(rightsId, encryptedData, dataHash);
        
        // Try to add with invalid share percentage
        vm.expectRevert("Invalid share percentage");
        royaltyManager.addRoyaltySplit(
            rightsId,
            payable(licensee),
            10001 // More than 100%
        );
    }

    function test_RevertWhen_TotalSharesExceed100() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");
        
        // First register rights in RightsVault
        rightsVault.registerRights(rightsId, encryptedData, dataHash);
        
        // Add first royalty split
        royaltyManager.addRoyaltySplit(
            rightsId,
            payable(licensee),
            8000 // 80% royalty rate
        );

        // Try to add second royalty split that would exceed 100%
        vm.expectRevert("Total shares exceed 100%");
        royaltyManager.addRoyaltySplit(
            rightsId,
            payable(user),
            3000 // 30% royalty rate
        );
    }

    function test_RevertWhen_NonOwnerAddsRoyaltySplit() public {
        bytes32 rightsId = keccak256("testRights");
        bytes32 encryptedData = keccak256("encryptedData");
        bytes32 dataHash = keccak256("dataHash");
        
        // First register rights in RightsVault
        rightsVault.registerRights(rightsId, encryptedData, dataHash);
        
        // Try to add royalty split as non-owner
        vm.prank(user);
        vm.expectRevert("Not rights owner");
        royaltyManager.addRoyaltySplit(
            rightsId,
            payable(licensee),
            1000 // 10% royalty rate
        );
    }

    // Add receive function to accept ETH refunds
    receive() external payable {}
} 