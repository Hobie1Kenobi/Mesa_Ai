#!/bin/bash

# Verify RightsVault contract
echo "Verifying RightsVault contract..."
forge verify-contract \
    --chain-id 84532 \
    --watch \
    --constructor-args $(cast abi-encode "constructor()") \
    0xC2aC41FBB401B5620133Ff94606F758DbF750517 \
    src/RightsVault.sol:RightsVault \
    --etherscan-api-key ${BASESCAN_API_KEY}

# Add verification for other contracts here if needed 