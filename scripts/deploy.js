// Script to deploy MusicRightsVault and VerificationRegistry contracts

const hre = require("hardhat");

async function main() {
  console.log("Starting deployment process...");

  // Deploy MusicRightsVault
  console.log("Deploying MusicRightsVault...");
  const MusicRightsVault = await hre.ethers.getContractFactory("MusicRightsVault");
  const musicRightsVault = await MusicRightsVault.deploy();
  await musicRightsVault.deployed();
  console.log(`MusicRightsVault deployed to: ${musicRightsVault.address}`);

  // Deploy VerificationRegistry
  console.log("Deploying VerificationRegistry...");
  const VerificationRegistry = await hre.ethers.getContractFactory("VerificationRegistry");
  const verificationRegistry = await VerificationRegistry.deploy();
  await verificationRegistry.deployed();
  console.log(`VerificationRegistry deployed to: ${verificationRegistry.address}`);

  // Print summary
  console.log("\nDeployment Summary:");
  console.log("==================");
  console.log(`Network: ${hre.network.name}`);
  console.log(`MusicRightsVault: ${musicRightsVault.address}`);
  console.log(`VerificationRegistry: ${verificationRegistry.address}`);
  console.log("==================");

  // Wait for a minute to allow Etherscan to index the contracts
  console.log("\nWaiting for block explorer to index the contracts...");
  await new Promise(resolve => setTimeout(resolve, 60000));

  // Verify contracts on Etherscan
  if (hre.network.name !== "hardhat" && hre.network.name !== "localhost") {
    console.log("\nVerifying contracts on block explorer...");
    
    try {
      await hre.run("verify:verify", {
        address: musicRightsVault.address,
        constructorArguments: [],
      });
      console.log("MusicRightsVault verified successfully");
    } catch (error) {
      console.error("Error verifying MusicRightsVault:", error.message);
    }

    try {
      await hre.run("verify:verify", {
        address: verificationRegistry.address,
        constructorArguments: [],
      });
      console.log("VerificationRegistry verified successfully");
    } catch (error) {
      console.error("Error verifying VerificationRegistry:", error.message);
    }
  }

  console.log("\nDeployment completed!");
}

// Execute the deployment
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  }); 