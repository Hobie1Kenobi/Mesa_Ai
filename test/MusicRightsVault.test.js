const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("MusicRightsVault", function () {
  let musicRightsVault;
  let owner;
  let verifier;
  let musician;
  let buyer;
  
  // Sample data
  const rightId = ethers.utils.id("music-right-1");
  const metadataHash = ethers.utils.id("metadata-hash-1");
  const sampleProof = ethers.utils.hexlify(ethers.utils.randomBytes(32));
  
  beforeEach(async function () {
    // Get signers
    [owner, verifier, musician, buyer] = await ethers.getSigners();
    
    // Deploy contract
    const MusicRightsVault = await ethers.getContractFactory("MusicRightsVault");
    musicRightsVault = await MusicRightsVault.deploy();
    await musicRightsVault.deployed();
    
    // Add verifier
    await musicRightsVault.addVerifier(verifier.address);
  });
  
  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      expect(await musicRightsVault.owner()).to.equal(owner.address);
    });
    
    it("Should set the owner as an authorized verifier", async function () {
      expect(await musicRightsVault.authorizedVerifiers(owner.address)).to.be.true;
    });
  });
  
  describe("Verifier Management", function () {
    it("Should add a verifier", async function () {
      expect(await musicRightsVault.authorizedVerifiers(verifier.address)).to.be.true;
    });
    
    it("Should remove a verifier", async function () {
      await musicRightsVault.removeVerifier(verifier.address);
      expect(await musicRightsVault.authorizedVerifiers(verifier.address)).to.be.false;
    });
    
    it("Should fail if non-owner tries to add a verifier", async function () {
      await expect(
        musicRightsVault.connect(musician).addVerifier(buyer.address)
      ).to.be.revertedWith("Only owner can call this function");
    });
  });
  
  describe("Right Registration", function () {
    it("Should register a new right", async function () {
      await musicRightsVault.connect(musician).registerRight(rightId, metadataHash);
      expect(await musicRightsVault.getRightMetadataHash(rightId)).to.equal(metadataHash);
    });
    
    it("Should fail to register a right that already exists", async function () {
      await musicRightsVault.connect(musician).registerRight(rightId, metadataHash);
      await expect(
        musicRightsVault.connect(musician).registerRight(rightId, metadataHash)
      ).to.be.revertedWith("Right ID already exists");
    });
  });
  
  describe("Right Verification", function () {
    beforeEach(async function () {
      await musicRightsVault.connect(musician).registerRight(rightId, metadataHash);
    });
    
    it("Should verify a right", async function () {
      await musicRightsVault.connect(verifier).verifyRight(rightId);
      expect(await musicRightsVault.isRightVerified(rightId)).to.be.true;
    });
    
    it("Should fail if non-verifier tries to verify a right", async function () {
      await expect(
        musicRightsVault.connect(musician).verifyRight(rightId)
      ).to.be.revertedWith("Only authorized verifiers can call this function");
    });
    
    it("Should fail to verify a non-existent right", async function () {
      const nonExistentRightId = ethers.utils.id("non-existent");
      await expect(
        musicRightsVault.connect(verifier).verifyRight(nonExistentRightId)
      ).to.be.revertedWith("Right does not exist");
    });
    
    it("Should fail to verify an already verified right", async function () {
      await musicRightsVault.connect(verifier).verifyRight(rightId);
      await expect(
        musicRightsVault.connect(verifier).verifyRight(rightId)
      ).to.be.revertedWith("Right already verified");
    });
  });
  
  describe("Right Ownership", function () {
    beforeEach(async function () {
      await musicRightsVault.connect(musician).registerRight(rightId, metadataHash);
    });
    
    it("Should return rights owned by an address", async function () {
      const rights = await musicRightsVault.connect(musician).getMyRights();
      expect(rights.length).to.equal(1);
      expect(rights[0]).to.equal(rightId);
    });
    
    it("Should transfer a right to another address", async function () {
      await musicRightsVault.connect(musician).transferRight(rightId, buyer.address);
      
      // Musician shouldn't have the right anymore
      const musicianRights = await musicRightsVault.connect(musician).getMyRights();
      expect(musicianRights.length).to.equal(0);
      
      // Buyer should now have the right
      const buyerRights = await musicRightsVault.connect(buyer).getMyRights();
      expect(buyerRights.length).to.equal(1);
      expect(buyerRights[0]).to.equal(rightId);
    });
    
    it("Should fail if trying to transfer a right not owned", async function () {
      await expect(
        musicRightsVault.connect(buyer).transferRight(rightId, owner.address)
      ).to.be.revertedWith("Sender does not own this right");
    });
  });
  
  describe("Zero-Knowledge Proof", function () {
    it("Should accept a valid proof", async function () {
      // This is a placeholder test for the ZK proof functionality
      expect(await musicRightsVault.submitOwnershipProof(sampleProof)).to.be.true;
    });
    
    it("Should reject an empty proof", async function () {
      await expect(
        musicRightsVault.submitOwnershipProof("0x")
      ).to.be.revertedWith("Proof cannot be empty");
    });
  });
}); 