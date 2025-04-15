/**
 * MESA AI Guardian Catalog Import Tool
 * 
 * This script demonstrates importing a music publisher's catalog from CSV
 * and registering the rights on the blockchain through our smart contracts.
 */

const fs = require('fs');
const csv = require('csv-parser');
const { ethers } = require('ethers');
const crypto = require('crypto');
require('dotenv').config();

// Contract ABIs and addresses
const musicRightsVaultABI = require('../build/contracts/MusicRightsVault.json').abi;
const verificationRegistryABI = require('../build/contracts/VerificationRegistry.json').abi;
const royaltyManagerABI = require('../build/contracts/RoyaltyManager.json').abi;

// Contract addresses on Base Sepolia
const MUSIC_RIGHTS_VAULT_ADDRESS = '0xD08BC592446e6cb5A85D5c9e84b928Fa55dDF315';
const VERIFICATION_REGISTRY_ADDRESS = '0x8c9f21191F29Ad6f6479134E1b9dA0907c3A1Ed5';
const ROYALTY_MANAGER_ADDRESS = '0xf76d44e87cd3EC26e8018Fd5aE1722A70D17d8b0';

// Connect to provider and set up wallet
// For demo purposes, we'll use an admin wallet that handles batch transactions
const provider = new ethers.providers.JsonRpcProvider(process.env.BASE_SEPOLIA_RPC_URL);
const wallet = new ethers.Wallet(process.env.ADMIN_PRIVATE_KEY, provider);

// Contract instances
const musicRightsVault = new ethers.Contract(
  MUSIC_RIGHTS_VAULT_ADDRESS,
  musicRightsVaultABI,
  wallet
);

const verificationRegistry = new ethers.Contract(
  VERIFICATION_REGISTRY_ADDRESS,
  verificationRegistryABI,
  wallet
);

const royaltyManager = new ethers.Contract(
  ROYALTY_MANAGER_ADDRESS,
  royaltyManagerABI,
  wallet
);

// Track stats for the import
const stats = {
  totalTracks: 0,
  processed: 0,
  succeeded: 0,
  failed: 0,
  totalGasCost: ethers.BigNumber.from(0),
  startTime: 0,
  endTime: 0
};

/**
 * Generate a unique rights ID for a track based on its metadata
 */
function generateRightsId(track) {
  const idString = `${track.ISRC}-${track['Track Title']}-${track['Primary Artist']}`;
  return ethers.utils.keccak256(ethers.utils.toUtf8Bytes(idString));
}

/**
 * Create encrypted data blob for on-chain storage (simulated)
 * In a real implementation, this would use proper encryption
 */
function createEncryptedData(track) {
  // In a real implementation, we would encrypt this data
  // For demo purposes, we'll just hash it to simulate encryption
  const trackData = JSON.stringify(track);
  return ethers.utils.keccak256(ethers.utils.toUtf8Bytes(trackData));
}

/**
 * Create a data hash for verification purposes
 */
function createDataHash(track) {
  const importantFields = [
    track.ISRC,
    track.ISWC,
    track['Track Title'],
    track['Primary Artist'],
    track['Songwriter 1'],
    track['Songwriter 1 Split'],
    track['Songwriter 2'],
    track['Songwriter 2 Split'],
    track['Songwriter 3'],
    track['Songwriter 3 Split'],
  ].filter(Boolean).join('-');
  
  return ethers.utils.keccak256(ethers.utils.toUtf8Bytes(importantFields));
}

/**
 * Register a track on the blockchain
 */
async function registerTrack(track) {
  try {
    const rightsId = generateRightsId(track);
    const encryptedData = createEncryptedData(track);
    const dataHash = createDataHash(track);
    
    console.log(`Registering track: ${track['Track Title']} by ${track['Primary Artist']}`);
    console.log(`Rights ID: ${rightsId}`);
    
    // Prepare music-specific metadata
    const mesaTrackId = track.ISRC || track.ISWC || `MESA-${Date.now()}`;
    const title = track['Track Title'];
    const artist = track['Primary Artist'];
    const releaseYear = parseInt(track['Release Year']) || 2023;
    const rightsTypes = ['MechanicalRights', 'PerformanceRights'];
    
    // For demo purposes, we'll simulate this transaction
    console.log('Simulating blockchain transaction...');
    
    // In a real implementation, this would be an actual transaction:
    /*
    const tx = await musicRightsVault.registerMusicRights(
      rightsId,
      encryptedData,
      dataHash,
      mesaTrackId,
      title,
      artist,
      releaseYear,
      rightsTypes,
      { gasLimit: 500000 }
    );
    
    const receipt = await tx.wait();
    const gasUsed = receipt.gasUsed;
    stats.totalGasCost = stats.totalGasCost.add(gasUsed);
    console.log(`Transaction complete. Gas used: ${gasUsed.toString()}`);
    console.log(`Transaction hash: ${receipt.transactionHash}`);
    */
    
    // Simulate a successful transaction for demo
    await new Promise(resolve => setTimeout(resolve, 500)); // Simulate blockchain delay
    
    console.log('✅ Rights registered successfully on the blockchain');
    stats.succeeded++;
    
    // If there are multiple songwriters, set up royalty splits
    const songwriters = [];
    const splits = [];
    
    if (track['Songwriter 1'] && track['Songwriter 1 Split']) {
      songwriters.push(track['Songwriter 1']);
      splits.push(parseInt(track['Songwriter 1 Split']));
    }
    
    if (track['Songwriter 2'] && track['Songwriter 2 Split']) {
      songwriters.push(track['Songwriter 2']);
      splits.push(parseInt(track['Songwriter 2 Split']));
    }
    
    if (track['Songwriter 3'] && track['Songwriter 3 Split']) {
      songwriters.push(track['Songwriter 3']);
      splits.push(parseInt(track['Songwriter 3 Split']));
    }
    
    if (songwriters.length > 1) {
      console.log(`Setting up royalty splits for ${songwriters.length} songwriters`);
      // In a real implementation, this would call the royalty manager contract
      // For demo, we'll just log the splits
      songwriters.forEach((writer, index) => {
        console.log(`  ${writer}: ${splits[index]}%`);
      });
    }
    
    return true;
  } catch (error) {
    console.error(`❌ Error registering track ${track['Track Title']}:`, error.message);
    stats.failed++;
    return false;
  }
}

/**
 * Process the entire catalog file
 */
async function processCatalog(filePath) {
  const tracks = [];
  
  // First, read all tracks from the CSV
  await new Promise((resolve, reject) => {
    fs.createReadStream(filePath)
      .pipe(csv())
      .on('data', (data) => tracks.push(data))
      .on('end', resolve)
      .on('error', reject);
  });
  
  stats.totalTracks = tracks.length;
  stats.startTime = Date.now();
  
  console.log(`=== MESA AI Guardian Catalog Import ===`);
  console.log(`Starting import of ${stats.totalTracks} tracks from ${filePath}`);
  console.log(`Target blockchain: Base Sepolia Testnet`);
  console.log(`Music Rights Vault: ${MUSIC_RIGHTS_VAULT_ADDRESS}`);
  console.log(`Verification Registry: ${VERIFICATION_REGISTRY_ADDRESS}`);
  console.log(`Royalty Manager: ${ROYALTY_MANAGER_ADDRESS}`);
  console.log(`===================================`);
  
  // Process tracks in batches to simulate bulk registration
  const BATCH_SIZE = 5;
  
  for (let i = 0; i < tracks.length; i += BATCH_SIZE) {
    const batch = tracks.slice(i, i + BATCH_SIZE);
    console.log(`\nProcessing batch ${Math.floor(i/BATCH_SIZE) + 1} of ${Math.ceil(tracks.length/BATCH_SIZE)}`);
    console.log(`--------------------------`);
    
    // Process tracks in this batch concurrently
    await Promise.all(batch.map(async (track) => {
      await registerTrack(track);
      stats.processed++;
      console.log(`Progress: ${stats.processed}/${stats.totalTracks} tracks processed`);
    }));
    
    // In a real implementation with actual blockchain transactions,
    // we might want to process batches sequentially instead of concurrently
    // to avoid nonce issues
  }
  
  stats.endTime = Date.now();
  
  displaySummary();
}

/**
 * Display a summary of the import process
 */
function displaySummary() {
  const durationSeconds = (stats.endTime - stats.startTime) / 1000;
  
  console.log(`\n=== Import Summary ===`);
  console.log(`Total tracks: ${stats.totalTracks}`);
  console.log(`Successfully registered: ${stats.succeeded}`);
  console.log(`Failed: ${stats.failed}`);
  console.log(`Success rate: ${((stats.succeeded / stats.totalTracks) * 100).toFixed(2)}%`);
  console.log(`Total duration: ${durationSeconds.toFixed(2)} seconds`);
  console.log(`Average time per track: ${(durationSeconds / stats.totalTracks).toFixed(2)} seconds`);
  // In a real implementation, we would show actual gas costs
  // console.log(`Total gas used: ${ethers.utils.formatUnits(stats.totalGasCost, 'gwei')} gwei`);
  console.log(`===================================`);
}

// Execute the import process
const catalogPath = process.argv[2] || '../MESA_DEMO_CATALOG.csv';

processCatalog(catalogPath)
  .then(() => {
    console.log('Catalog import completed');
    // In a real implementation, we might want to generate a report
  })
  .catch(error => {
    console.error('Error during catalog import:', error);
    process.exit(1);
  }); 