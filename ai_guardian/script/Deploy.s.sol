// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Script.sol";
import "../src/RightsVault.sol";
import "../src/MusicRightsVault.sol";
import "../src/VerificationRegistry.sol";
import "../src/EnhancedVerification.sol";
import "../src/RoyaltyManager.sol";
import "../src/UsageTracker.sol";

contract DeployScript is Script {
    function run() external {
        // Retrieve the private key from environment variable
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        // Start broadcasting transactions
        vm.startBroadcast(deployerPrivateKey);

        // Deploy RightsVault first as it's the base contract
        RightsVault rightsVault = new RightsVault();
        console.log("RightsVault deployed at:", address(rightsVault));

        // Deploy MusicRightsVault which inherits from RightsVault
        MusicRightsVault musicRightsVault = new MusicRightsVault();
        console.log("MusicRightsVault deployed at:", address(musicRightsVault));

        // Deploy VerificationRegistry
        VerificationRegistry verificationRegistry = new VerificationRegistry();
        console.log("VerificationRegistry deployed at:", address(verificationRegistry));

        // Deploy EnhancedVerification with RightsVault address
        EnhancedVerification enhancedVerification = new EnhancedVerification(address(rightsVault));
        console.log("EnhancedVerification deployed at:", address(enhancedVerification));

        // Deploy RoyaltyManager with RightsVault address
        RoyaltyManager royaltyManager = new RoyaltyManager(address(rightsVault));
        console.log("RoyaltyManager deployed at:", address(royaltyManager));

        // Deploy UsageTracker with RightsVault address
        UsageTracker usageTracker = new UsageTracker(address(rightsVault));
        console.log("UsageTracker deployed at:", address(usageTracker));

        vm.stopBroadcast();
    }
} 