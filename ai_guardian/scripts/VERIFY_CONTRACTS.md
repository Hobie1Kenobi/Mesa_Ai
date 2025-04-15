# Contract Verification Instructions

This guide will help you verify the MESA Rights Vault contracts on BaseScan.

## Prerequisites

1. A BaseScan API key (get one from [https://basescan.org/apis](https://basescan.org/apis))
2. Python 3.6+ installed
3. The contract source code and deployment information

## Step 1: Set Up Your Environment

1. Add your BaseScan API key to the `.env` file:
   ```
   BASESCAN_API_KEY=your_api_key_here
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements_verify.txt
   ```

## Step 2: Run the Verification Script

Run the verification script:
```
python verify_contracts.py
```

This script will:
- Verify all contracts in the correct order
- Submit the source code and compiler settings to BaseScan
- Provide feedback on the verification process

## Step 3: Check Verification Status

After running the script, check the verification status on BaseScan:
- RightsVault: [https://sepolia.basescan.org/address/0xC2aC41FBB401B5620133Ff94606F758DbF750517#code](https://sepolia.basescan.org/address/0xC2aC41FBB401B5620133Ff94606F758DbF750517#code)
- MusicRightsVault: [https://sepolia.basescan.org/address/0x242a151FBEdb95Fbd8Cf06d8e382cc15753C998F#code](https://sepolia.basescan.org/address/0x242a151FBEdb95Fbd8Cf06d8e382cc15753C998F#code)
- VerificationRegistry: [https://sepolia.basescan.org/address/0x27150B841827Dada42cddebF1dD2cC927b3c41a1#code](https://sepolia.basescan.org/address/0x27150B841827Dada42cddebF1dD2cC927b3c41a1#code)
- EnhancedVerification: [https://sepolia.basescan.org/address/0xceC0EF695E2f6fff4147aCB7158FF829d7351556#code](https://sepolia.basescan.org/address/0xceC0EF695E2f6fff4147aCB7158FF829d7351556#code)
- UsageTracker: [https://sepolia.basescan.org/address/0x64C98696058AFcFa6fB75D1173b1a275fCed41C9#code](https://sepolia.basescan.org/address/0x64C98696058AFcFa6fB75D1173b1a275fCed41C9#code)
- RoyaltyManager: [https://sepolia.basescan.org/address/0x4A3531D6B3d5a2e4CcAEE26A41D1E7c88D9b2Fa5#code](https://sepolia.basescan.org/address/0x4A3531D6B3d5a2e4CcAEE26A41D1E7c88D9b2Fa5#code)

## Manual Verification (if needed)

If the automated verification fails, you can verify contracts manually:

1. Go to [https://sepolia.basescan.org/verifyContract](https://sepolia.basescan.org/verifyContract)
2. Enter the contract address
3. Enter the contract name (e.g., "RightsVault")
4. Select "Solidity (Single file)" as the compiler type
5. Select "v0.8.19+commit.7dd6d404" as the compiler version
6. Enable optimization with 200 runs
7. Paste the contract source code
8. Leave constructor arguments empty (or provide them if the contract has constructor parameters)
9. Click "Verify & Publish"

## Troubleshooting

- **API Key Issues**: Make sure your BaseScan API key is correct and has sufficient credits
- **Compiler Version Mismatch**: Ensure you're using the same compiler version as used for deployment
- **Optimization Settings**: Verify that the optimization settings match those used during deployment
- **Constructor Arguments**: For contracts with constructor arguments, you need to provide the ABI-encoded arguments

## Contract Details

| Contract | Address | Constructor Args |
|----------|---------|-----------------|
| RightsVault | 0xC2aC41FBB401B5620133Ff94606F758DbF750517 | None |
| MusicRightsVault | 0x242a151FBEdb95Fbd8Cf06d8e382cc15753C998F | RightsVault address |
| VerificationRegistry | 0x27150B841827Dada42cddebF1dD2cC927b3c41a1 | None |
| EnhancedVerification | 0xceC0EF695E2f6fff4147aCB7158FF829d7351556 | RightsVault address |
| UsageTracker | 0x64C98696058AFcFa6fB75D1173b1a275fCed41C9 | RightsVault address |
| RoyaltyManager | 0x4A3531D6B3d5a2e4CcAEE26A41D1E7c88D9b2Fa5 | RightsVault address | 