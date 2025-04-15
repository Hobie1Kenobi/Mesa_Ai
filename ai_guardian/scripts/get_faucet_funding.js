const { ethers } = require('ethers');
require('dotenv').config();

// Function to check wallet balance
async function checkWalletBalance() {
  try {
    // Connect to Base Sepolia
    const provider = new ethers.providers.JsonRpcProvider('https://sepolia.base.org');
    
    // Load wallet from private key in .env
    const privateKey = process.env.MESA_PRIVATE_KEY || process.env.PRIVATE_KEY;
    if (!privateKey) {
      console.error('❌ No private key found in .env file. Please add PRIVATE_KEY=your_private_key to your .env file.');
      process.exit(1);
    }
    
    const wallet = new ethers.Wallet(privateKey, provider);
    const address = await wallet.getAddress();
    
    // Get and display balance
    const balance = await provider.getBalance(address);
    const etherBalance = ethers.utils.formatEther(balance);
    
    console.log('\n=== MESA Wallet Information ===');
    console.log(`Address: ${address}`);
    console.log(`Balance: ${etherBalance} Base Sepolia ETH`);
    
    // Check if balance is low
    if (parseFloat(etherBalance) < 0.01) {
      console.log('\n⚠️ Your wallet balance is low! You need to get some Base Sepolia ETH.');
      displayFaucetOptions(address);
    } else {
      console.log('\n✅ Your wallet has sufficient balance for testing.');
    }
    
    return { address, balance };
  } catch (error) {
    console.error(`❌ Error checking wallet balance: ${error.message}`);
    process.exit(1);
  }
}

// Function to display faucet options
function displayFaucetOptions(address) {
  console.log('\n=== Faucet Options for Base Sepolia ===');
  console.log('Copy your address: ' + address);
  console.log('\n1. Coinbase Base Faucet');
  console.log('   URL: https://www.coinbase.com/faucets/base-sepolia-faucet');
  console.log('   - Connect your wallet or paste your address');
  console.log('   - Complete the captcha');
  console.log('   - Click "Send test ETH"');
  
  console.log('\n2. Paradigm Faucet');
  console.log('   URL: https://faucet.paradigm.xyz/');
  console.log('   - Select "Base Sepolia"');
  console.log('   - Paste your address');
  console.log('   - Complete the captcha');
  
  console.log('\n3. 0xCecf Drip Faucet');
  console.log('   URL: https://0xDb6026B5BB6553eb793B76A5742B56742c354dF5@drip.0xcecf.xyz/');
  console.log('   - Paste your address');
  console.log('   - Submit the form');
  
  console.log('\nAfter receiving funds, run this script again to verify your balance has been updated.');
  console.log('Once you have funds, you can continue with your deployments and attestations.');
}

// Function to prepare a faucet request URL
function prepareFaucetUrl(address) {
  // This generates shareable URLs where possible
  const urls = [
    `https://www.coinbase.com/faucets/base-sepolia-faucet`, // Coinbase doesn't have a direct URL with address
    `https://faucet.paradigm.xyz/?chain=base_sepolia&address=${address}`, // Paradigm accepts address in URL
    `https://drip.0xcecf.xyz/?address=${address}&network=base-sepolia` // 0xCecf format
  ];
  
  return urls;
}

// Main function
async function main() {
  console.log('===== Base Sepolia Faucet Helper =====');
  console.log('This script helps you get testnet ETH for your MESA wallet');
  
  // Check current balance
  const { address, balance } = await checkWalletBalance();
  
  // If balance is sufficient, exit
  if (parseFloat(ethers.utils.formatEther(balance)) >= 0.01) {
    return;
  }
  
  // Prepare faucet URLs
  const faucetUrls = prepareFaucetUrl(address);
  
  console.log('\n=== Quick Access URLs ===');
  console.log('Open these URLs in your browser:');
  faucetUrls.forEach((url, index) => {
    console.log(`${index + 1}. ${url}`);
  });
  
  console.log('\nNote: Most faucets require CAPTCHA or other verification that cannot be automated.');
  console.log('After receiving funds, run this script again to check your updated balance.');
}

// Run the main function
main().catch(error => {
  console.error(`❌ An error occurred: ${error.message}`);
  process.exit(1); 
}); 