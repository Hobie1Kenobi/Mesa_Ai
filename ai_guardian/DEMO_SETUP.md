# MESA AI Guardian Demo Setup Guide

This guide will help you set up and run the MESA AI Guardian demo, showcasing the publisher-first approach for blockchain-enhanced music rights management.

## Prerequisites

- Node.js (v16+)
- npm or yarn
- An Ethereum wallet with Base Sepolia testnet ETH (for transaction fees)
- Base Sepolia RPC URL (from Alchemy, Infura, or similar provider)

## Demo Components

1. **Sample Music Catalog**: `MESA_DEMO_CATALOG.csv` contains a realistic publisher catalog for demo purposes
2. **Catalog Import Tool**: `tools/catalog_import.js` demonstrates batch importing of catalog data
3. **Publisher Dashboard**: `frontend/pages/publisher-dashboard.tsx` showcases the UI for publishers

## Setup Instructions

### 1. Environment Configuration

Create a `.env` file in the project root with the following:

```
BASE_SEPOLIA_RPC_URL=https://sepolia.base.org
ADMIN_PRIVATE_KEY=your_private_key_here  # Use a test wallet, not your main wallet!
MUSIC_RIGHTS_VAULT_ADDRESS=0xD08BC592446e6cb5A85D5c9e84b928Fa55dDF315
VERIFICATION_REGISTRY_ADDRESS=0x8c9f21191F29Ad6f6479134E1b9dA0907c3A1Ed5
ROYALTY_MANAGER_ADDRESS=0xf76d44e87cd3EC26e8018Fd5aE1722A70D17d8b0
```

### 2. Install Dependencies

```bash
# For the backend/tools
npm install ethers@5.7.2 csv-parser dotenv

# For the frontend
cd frontend
npm install
cd ..
```

## Running the Demo

### Option 1: Catalog Import Demo (Backend)

This demonstrates how a publisher could batch-import their catalog:

```bash
node tools/catalog_import.js
```

You'll see the script:
1. Read the sample catalog CSV
2. Process tracks in batches
3. Generate unique rights IDs
4. "Register" each track on the blockchain (simulated)
5. Set up royalty splits based on songwriter percentages
6. Output success/failure statistics

### Option 2: Publisher Dashboard (Frontend)

This shows the UI that publishers would interact with:

```bash
cd frontend
npm run dev
```

Visit `http://localhost:3000/publisher-dashboard` to see:
1. Catalog overview and statistics
2. Import functionality (click "Import Catalog" to see a simulated import)
3. Track management interface
4. Filtering and search capabilities

## Customizing the Demo

### Using Your Own Catalog

Replace our sample catalog with your own:

1. Format your data in CSV with the same column structure as `MESA_DEMO_CATALOG.csv`
2. Save it in the project root
3. Run the import tool with your file: `node tools/catalog_import.js path/to/your/catalog.csv`

### Making Real Blockchain Transactions

By default, the import tool simulates transactions. To perform actual blockchain transactions:

1. Ensure your `.env` file has the correct values
2. In `catalog_import.js`, uncomment the real transaction code block (search for "In a real implementation")
3. Comment out the simulation code

## Demo Narrative

When presenting this demo for the hackathon, you can use this narrative:

1. **Problem Introduction**:
   "Traditional music rights management requires complex paperwork and lacks transparency. Artists and publishers need a secure way to register and verify rights."

2. **Solution Overview**:
   "MESA AI Guardian provides blockchain-enhanced rights management that works with existing industry workflows. Publishers can secure entire catalogs without requiring technical blockchain knowledge."

3. **Demo Walkthrough**:
   - Show the original catalog data (familiar CSV format)
   - Run the import process, highlighting how it handles batch processing
   - Display the dashboard with registered works
   - Emphasize the transparency and immutability of the blockchain records

4. **Key Benefits**:
   - No technical blockchain knowledge required for publishers
   - Familiar workflows with enhanced security
   - Bulk operations for efficiency
   - Complete audit trail of rights registrations

## Troubleshooting

If you encounter issues during the demo:

- **Connection errors**: Check your RPC URL in the `.env` file
- **Transaction errors**: Ensure your wallet has Base Sepolia ETH
- **Import failures**: Verify the CSV format matches the expected structure

For additional support, refer to the smart contract documentation or contact the development team.

---

This demo showcases how MESA AI Guardian makes blockchain technology accessible to publishers without requiring end-users to understand the underlying technical details. 