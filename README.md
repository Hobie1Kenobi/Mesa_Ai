# MESA Rights Vault

![MESA Rights Vault](https://i.imgur.com/JuP5ULl.png)

> **Privacy-focused music rights management on the Base blockchain**

## The Problem

The music industry faces significant challenges with rights management:

- **Lack of Transparency**: Artists often don't know who owns their rights or how they're being used
- **Privacy Concerns**: Sensitive contract details need protection while enabling verification
- **Inefficient Verification**: Platforms struggle to verify rights ownership without exposing private data
- **Technical Barriers**: Blockchain solutions exist but are too complex for most artists

## Our Solution

MESA Rights Vault is a privacy-first system for registering and verifying music rights on the Base blockchain. It combines AI-powered contract analysis with zero-knowledge proofs and blockchain technology to create a secure, private, and efficient rights management system.

### Key Components

- **AI Guardian**: Analyzes music contracts to extract key rights information
- **Privacy Layer**: Protects sensitive data using encryption and zero-knowledge proofs
- **Blockchain Registry**: Stores verifiable proofs on the Base Sepolia blockchain
- **Verification System**: Allows platforms to verify rights without exposing private details

## How It Works

### For Artists & Rights Holders

1. **Upload Contracts**: Submit your music contracts to the AI Guardian system
2. **Review Analysis**: Our AI extracts critical information about your rights
3. **Register On-chain**: Your rights are recorded on Base blockchain with privacy protection
4. **Share Securely**: Provide verifiable proof of your rights without exposing sensitive details

### For Music Platforms

1. **Request Verification**: Ask to verify rights for specific content
2. **Receive Proof**: Get cryptographic proof of rights ownership
3. **Verify On-chain**: Confirm the proof matches the registered data on Base
4. **Respect Privacy**: Complete the verification without seeing private contract terms

## Progress Made

- ✅ Deployed RightsVault smart contract on Base Sepolia testnet
- ✅ Integrated Ollama's local LLM for contract analysis
- ✅ Implemented basic encryption for sensitive contract data
- ✅ Created sample contracts and successful extraction pipeline
- ✅ Built integration with MESA Track ID system for metadata validation
- ✅ Designed initial zero-knowledge proof concepts

## Technical Details

### Smart Contracts

Our RightsVault.sol contract is deployed on Base Sepolia at: `0x7338af1E9d6dbc4cc1Efa067C0775Bf222aDb0C3`

The contract stores:
- Rights holder identifiers
- Rights types (Publishing, Performance, Mechanical, Sync)
- Territory information
- Proof verification data

### AI Guardian

Uses Ollama's local LLM to:
- Extract key terms from legal contracts
- Transform unstructured text into structured data
- Handle multiple contract types (producer agreements, publishing deals, etc.)

### Privacy Layer

Implements:
- Data encryption for sensitive contract details
- Selective disclosure mechanisms
- Foundation for zero-knowledge proofs

### Integration Points

- **MESA Track ID System**: Validates music metadata accuracy
- **Base Blockchain**: Provides immutable rights registry
- **Web3.py**: Facilitates blockchain interactions

## See It In Action

```
# Sample verification workflow
$ python verify_rights.py --work "Song Title" --rights_type "Publishing"

> Verification request initiated for "Song Title"
> Generating zero-knowledge proof...
> Submitting verification to Base Sepolia...
> ✓ Rights verified! Publisher has publishing rights for this work.
> No sensitive contract details were revealed in this process.
```

## Setup & Installation

```bash
# Clone the repository
git clone https://github.com/your-org/mesa-rights-vault.git
cd mesa-rights-vault

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and wallet info

# Run the demo
python scripts/demo.py
```

## Common Tasks

### Register Music Rights

```bash
# Process a contract and register rights
python scripts/05_integrate_with_blockchain.py
```

### Verify Rights

```bash
# Verify rights for specific content
python scripts/verify_rights.py --work "Your Song Title"
```

## Troubleshooting

- **Contract Analysis Fails**: Ensure contract is in readable text format (.txt or .pdf)
- **Blockchain Errors**: Check your network connection and wallet configuration
- **Extraction Issues**: Try the mock data option to test the full pipeline

## Roadmap

See our [full roadmap](MESA_Base_Hackathon/ai_guardian/docs/future_roadmap.md) for upcoming features, including:

- Web dashboard for rights management
- Full zero-knowledge proof implementation
- Automated royalty distribution
- Integration with music streaming platforms

## Further Documentation

- [Smart Contract Documentation](MESA_Base_Hackathon/ai_guardian/contracts/README.md)
- [AI Guardian Guide](MESA_Base_Hackathon/ai_guardian/models/README.md)
- [Privacy Layer Specification](MESA_Base_Hackathon/ai_guardian/src/privacy/README.md)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Built with ❤️ by MESA for the Base Hackathon 