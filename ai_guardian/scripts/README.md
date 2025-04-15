# Base Sepolia EAS Attestation Script

This script creates a real music rights attestation on the Base Sepolia testnet using the Ethereum Attestation Service (EAS).

## Prerequisites

- Node.js installed (v14 or higher)
- Base Sepolia testnet ETH in your wallet
- A private key with some Base Sepolia ETH

## Setup Instructions

1. Install dependencies:
   ```
   npm install ethers@5.7.2 dotenv
   ```

2. Create a `.env` file in this directory with your private key:
   ```
   cp .env.example .env
   ```
   
3. Edit the `.env` file and add your private key

## Getting Base Sepolia Testnet ETH

You'll need some Base Sepolia testnet ETH to run this script. Here's how to get it:

1. Go to the [Base Faucet](https://www.coinbase.com/faucets/base-sepolia-faucet)
2. Connect your wallet
3. Request testnet ETH

Alternatively, you can use these other faucets:
- [Paradigm Faucet](https://faucet.paradigm.xyz/)
- [0xCecf Drip](https://0xDb6026B5BB6553eb793B76A5742B56742c354dF5@drip.0xcecf.xyz/)

## Running the Script

Execute the script with:

```
node create_eas_attestation.js
```

## Expected Output

The script will:

1. Register a schema for music rights attestations
2. Create an attestation for a sample music track
3. Output the attestation UID and transaction details
4. Provide a link to view the attestation on the Base Sepolia EAS Explorer

## Viewing Your Attestation

After the script runs successfully, you can view your attestation at:
https://base-sepolia.easscan.org/attestation/view/YOUR_ATTESTATION_UID

## Troubleshooting

- **"Private key not found"**: Make sure you've created a `.env` file with your private key
- **"Wallet has no ETH"**: Get testnet ETH from one of the faucets listed above
- **Transaction errors**: Make sure the Base Sepolia network is operating normally

## Using in Your Application

The attestation UID you receive can be used in your application to verify the music rights. 
Save this UID to link it with your track information in your database. 

## Test Run Results (BASE Hackathon Preparation)

We successfully completed a test run of our attestation system for the upcoming BASE Batches Hackathon. Here are the details:

### Test Attestation Details

- **Wallet Address**: 0xbDE22Ea0D5d21925f8c64d28c0b1a376763a76d8
- **Schema Used**: 0x14554977234f8ef97a88c5a1da6d65e8522922671b511b4aa5d198a4629de6b1
- **Music Asset**:
  - Title: "Summer Nights"
  - Artist: "John Doe"
  - Publisher: "MESA Music Publishing"
- **Attestation UID**: 0xb2802e2e80824a796b8179349f94c73485d4dbe27e30cb5f04f4b1cd36083495
- **Transaction Hash**: 0xb2802e2e80824a796b8179349f94c73485d4dbe27e30cb5f04f4b1cd36083495
- **Block Number**: 24462040
- **Gas Used**: 24096

### View The Attestation

Our test attestation can be viewed on the Base Sepolia EAS Explorer:
[View Attestation](https://base-sepolia.easscan.org/attestation/view/0xb2802e2e80824a796b8179349f94c73485d4dbe27e30cb5f04f4b1cd36083495)

### Next Steps for Mainnet Deployment

For the BASE Batches Hackathon, we'll follow this same process but will:

1. Update the script to use BASE mainnet contract addresses
2. Register a custom schema specifically for music rights data
3. Batch process the entire music catalog
4. Implement proper error handling and retry logic for production use

The test run confirms our approach works correctly and we're ready for the hackathon next week. 

## MESA Decentralized Identifier (DID) Attestation

We've also created a Decentralized Identifier (DID) attestation for MESA on the Base Sepolia testnet. This establishes MESA's official identity on the Base blockchain.

### MESA DID Script

The `create_mesa_did_attestation.js` script creates a DID attestation with:
- A unique identifier in the format `did:base:mesa:{uniqueId}`
- Official MESA branding information
- A visual representation ("tattoo") of MESA's blockchain identity
- Complete metadata about MESA's services

### MESA DID Attestation Details

- **DID**: `did:base:mesa:f00768d2fbd3`
- **Attestation UID**: `0x3cb41fc26c71dd39cbb0f88ab1a7b5b209c76a22238b1017e3fd59c4c17c6073`
- **Transaction Hash**: `0x3cb41fc26c71dd39cbb0f88ab1a7b5b209c76a22238b1017e3fd59c4c17c6073`
- **Block Number**: `24462334`
- **Website**: `https://www.mesawallet.io`
- **Brand Purpose**: Protecting music rights with professional splits contracts and work-for-hire agreements

### View The MESA DID Attestation

The DID attestation can be viewed on the Base Sepolia EAS Explorer:
[View MESA DID Attestation](https://base-sepolia.easscan.org/attestation/view/0x3cb41fc26c71dd39cbb0f88ab1a7b5b209c76a22238b1017e3fd59c4c17c6073)

## New Track Attestation

We've created an additional track attestation to demonstrate our system's ability to handle diverse music metadata.

### New Track Attestation Details

- **Wallet Address**: 0xbDE22Ea0D5d21925f8c64d28c0b1a376763a76d8
- **Schema Used**: 0x40aad7f118ba0f4f36c2036190fdc9df7b8bad9299744d5033ed843b1b00e0aa
- **Music Asset**:
  - Title: "Digital Harmony"
  - Artist: "Web3 Audio Project"
  - ISWC: "T-123456789-3"
  - Publisher: "Blockchain Beats Publishing"
- **Attestation UID**: 0x0eebe586e9d5afbfda184ff82833032767a5acedb21db8cb8fb8e26e2c9f9802
- **Transaction Hash**: 0x0eebe586e9d5afbfda184ff82833032767a5acedb21db8cb8fb8e26e2c9f9802
- **Block Number**: 24480829
- **Gas Used**: 26792

### View The New Track Attestation

The new track attestation can be viewed on the Base Sepolia EAS Explorer:
[View New Track Attestation](https://base-sepolia.easscan.org/attestation/view/0x0eebe586e9d5afbfda184ff82833032767a5acedb21db8cb8fb8e26e2c9f9802)

### Visual Identity

A unique visual representation of MESA's blockchain identity has been created and saved as `MESA_DID_visual_tattoo.svg`. This visual identifier combines:

1. MESA's branding elements
2. A unique pattern derived from the DID hash
3. The DID identifier text
4. MESA's commitment to "Protecting Music Rights On Base"

### Uses for MESA's DID

This DID can be used to:
1. Verify MESA's identity on the Base blockchain
2. Authenticate music rights attestations created by MESA
3. Establish trust with artists, collaborators, and industry partners
4. Build future blockchain-based verification and authentication services

### Running the DID Script

Execute the script with:

```
node create_mesa_did_attestation.js
```

For the BASE Batches Hackathon, we plan to upgrade this DID to the BASE mainnet and integrate it with our music rights verification system. 

## Updated MESA DID Attestation

We've created an updated Decentralized Identifier (DID) attestation for MESA using our current schema UID and updated branding logo.

### Updated MESA DID Script

The `updated_mesa_did_attestation.js` script uses the same schema as our music track attestations, creating a unified verification system where both DIDs and musical works can be verified together. This approach:

1. Unifies the verification process across all MESA-related attestations
2. Integrates organization identity verification with music rights verification
3. Showcases the flexibility of our attestation framework
4. Features the updated MESA branding with the new logo design

### Updated MESA DID Attestation Details

- **DID Format**: `did:base:mesa:{uniqueId}`
- **Schema Used**: 0x40aad7f118ba0f4f36c2036190fdc9df7b8bad9299744d5033ed843b1b00e0aa
- **Attestation UID**: 0xe6569ed16ba55f9028bc3a1946d26c7e52971df8ca4e487c8964ed075740beb1
- **Transaction Hash**: 0xe6569ed16ba55f9028bc3a1946d26c7e52971df8ca4e487c8964ed075740beb1
- **Block Number**: 24484176
- **Gas Used**: 62408
- **Visual Identity**: An updated visual representation saved as `MESA_Updated_DID_visual_tattoo.svg`

### View The Updated MESA DID Attestation

The updated DID attestation can be viewed on the Base Sepolia EAS Explorer:
[View Updated MESA DID Attestation](https://base-sepolia.easscan.org/attestation/view/0xe6569ed16ba55f9028bc3a1946d26c7e52971df8ca4e487c8964ed075740beb1)

### Visual Identity

A unique visual representation of MESA's blockchain identity has been created and saved as `MESA_Updated_DID_visual_tattoo.svg`. This visual identifier combines:

1. MESA's branding elements
2. A unique pattern derived from the DID hash
3. The DID identifier text
4. MESA's commitment to "Protecting Music Rights On Base"

### Uses for MESA's Updated DID

This updated DID can be used to:
1. Verify MESA's identity on the Base blockchain
2. Authenticate music rights attestations created by MESA
3. Establish trust with artists, collaborators, and industry partners
4. Build future blockchain-based verification and authentication services

### Running the Updated DID Script

Execute the script with:

```
node updated_mesa_did_attestation.js
```

For the BASE Batches Hackathon, we plan to upgrade this updated DID to the BASE mainnet and integrate it with our music rights verification system. 