# MESA AI Guardian

An AI-powered music rights attestation system that verifies and records music ownership claims on the Base blockchain using the Ethereum Attestation Service (EAS).

## Overview

MESA AI Guardian analyzes music catalogs to automatically generate and manage on-chain attestations, creating verifiable proof of ownership for music rights holders.

![MESA AI Guardian Workflow](https://i.imgur.com/placeholder.png)

## Features

- **AI-Powered CSV Analysis**: Automatically process music catalog data and extract attestable claims
- **Smart Schema Selection**: Recommend appropriate attestation schemas based on rights types
- **Attestation Automation**: Create on-chain attestations with minimal user input
- **Verification Engine**: Validate rights claims against existing attestations
- **Conflict Detection**: Identify and flag potential ownership conflicts

## Project Structure

```
attestation_ai/
├── agent/                 # AI agent components
│   ├── analyzer.js        # CSV analysis and classification
│   ├── recommender.js     # Schema recommendation engine
│   └── verifier.js        # Attestation verification logic
├── eas/                   # EAS integration components
│   ├── schemas.js         # Schema definitions and registration
│   ├── attestor.js        # Attestation creation
│   └── verify.js          # Verification functions
├── ui/                    # Simple UI components
│   ├── dashboard.html     # Main dashboard
│   ├── upload.html        # CSV upload interface
│   └── verify.html        # Verification interface
├── scripts/               # Utility scripts
│   ├── create_attestation.js  # Script to create attestations
│   └── sample_data/       # Sample CSV files
└── README.md              # This file
```

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- Base Sepolia testnet ETH (for creating attestations)
- A private key with Base Sepolia ETH

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   cd attestation_ai
   npm install
   ```
3. Set up your environment variables:
   ```
   cp .env.example .env
   ```
   Edit `.env` to add your private key and other settings

### Running the AI Guardian

1. Start the agent and server:
   ```
   npm start
   ```
2. Open your browser to `http://localhost:3000`
3. Upload a music catalog CSV
4. Follow the AI recommendations for attestation

## How It Works

1. **Upload**: Publishers upload their music catalog in CSV format
2. **Analysis**: The AI agent analyzes the catalog for attestable claims
3. **Recommendation**: AI suggests appropriate schemas and attestation strategies
4. **Creation**: System creates on-chain attestations through EAS on Base
5. **Verification**: Attestations are verified and linked to the catalog

## Use Cases

- **Record Labels**: Establish on-chain proof of catalog ownership
- **Publishers**: Create verifiable attestations for licensing rights
- **Artists**: Verify ownership of their creative works
- **Platforms**: Integrate verification for royalty distribution

## Technical Details

### EAS Integration

We use the Ethereum Attestation Service on Base Sepolia with the following contract addresses:

- EAS Contract: `0xC2679fBD37d54388Ce493F1DB75320D236e1815e`
- Schema Registry: `0x0a7E2Ff54e76B8E6659aedc9103FB21c038050D0`

### Schema Structure

Our primary schema for music rights attestation:

```
tuple(string title, string artist, string iswc, address rightsHolder, uint256 tokenId, string containerAddress)
```

### AI Components

The AI system uses:
- Natural language processing to understand catalog entries
- Classification to determine rights types
- Conflict detection algorithms to identify potential disputes

## Contributing

Contributions are welcome! Please check out our [contribution guidelines](CONTRIBUTING.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Base blockchain team for the testnet infrastructure
- EAS team for the attestation service
- Coinbase for the AgentKit framework 