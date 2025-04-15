# Base Sepolia Faucet Helper

This script helps you check your wallet balance on Base Sepolia testnet and provides guidance for getting testnet ETH from various faucets.

## Purpose

When developing and testing smart contracts on the Base Sepolia testnet, you need testnet ETH. This helper script:

1. Checks your wallet balance
2. Determines if you need more funds
3. Provides direct links to faucets
4. Displays instructions for using each faucet

## Prerequisites

- Node.js installed (v14 or higher)
- `.env` file with your private key as `PRIVATE_KEY` or `MESA_PRIVATE_KEY`
- Installed dependencies (`ethers` and `dotenv`)

## Setup

1. Ensure you have a `.env` file in the same directory with your private key:
   ```
   PRIVATE_KEY=your_private_key_here
   ```

2. Install dependencies if you haven't already:
   ```
   npm install ethers@5.7.2 dotenv
   ```

## Running the Script

Execute the script with:

```
node get_faucet_funding.js
```

## Features

- **Balance Check**: Displays your current Base Sepolia ETH balance
- **Automatic Low Balance Detection**: If your balance is below 0.01 ETH, provides faucet information
- **Multiple Faucet Options**: Links to Coinbase, Paradigm, and 0xCecf faucets
- **Direct Access URLs**: Generates ready-to-use URLs with your address pre-filled when possible

## Faucet Options

The script provides information for these Base Sepolia faucets:

1. **Coinbase Base Faucet**: https://www.coinbase.com/faucets/base-sepolia-faucet
2. **Paradigm Faucet**: https://faucet.paradigm.xyz/
3. **0xCecf Drip**: https://0xDb6026B5BB6553eb793B76A5742B56742c354dF5@drip.0xcecf.xyz/

## Security Notes

- Never share your private key or commit your `.env` file to repositories
- The script only reads your private key locally to check your balance; it never transmits it

## Troubleshooting

- **RPC Connection Issues**: If you have trouble connecting to the Base Sepolia RPC, add a custom RPC URL in your `.env` file:
  ```
  RPC_URL=your_custom_rpc_url
  ```

- **Connection Timeout**: Some RPC providers may have rate limiting. Try again later or use a different RPC provider.

---

For more information on Base Sepolia testnet, visit the [Base Documentation](https://docs.base.org). 