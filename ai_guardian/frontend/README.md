# MESA Rights Vault Frontend

This is the frontend application for the MESA Rights Vault system, a blockchain-based platform for managing music rights with privacy and security.

## Features

- Rights Management: Register and manage your music rights
- Verification: Verify rights ownership and status
- Usage Tracking: Monitor and validate music usage
- Royalty Management: Track and distribute royalties
- Enhanced Verification: Multi-signature verification system

## Tech Stack

- **Framework**: Next.js with TypeScript
- **Web3 Integration**: wagmi + viem
- **UI Components**: TailwindCSS + shadcn/ui
- **State Management**: React Query + Zustand
- **Wallet Connection**: RainbowKit

## Prerequisites

- Node.js 18.x or later
- npm 9.x or later
- A Web3 wallet (MetaMask, WalletConnect, etc.)
- WalletConnect Project ID (for RainbowKit)

## Getting Started

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd MESA_Base_Hackathon/ai_guardian/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables:
   - Copy `.env.local.example` to `.env.local`
   - Update the contract addresses and RPC URL if needed
   - Add your WalletConnect Project ID to `src/lib/web3.ts`

4. Run the development server:
   ```bash
   npm run dev
   ```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
frontend/
├── src/
│   ├── app/              # Next.js app directory
│   ├── components/       # React components
│   │   ├── ui/          # UI components
│   │   ├── contracts/   # Contract-specific components
│   │   └── layout/      # Layout components
│   ├── contracts/       # Contract ABIs and types
│   ├── hooks/           # Custom React hooks
│   └── lib/             # Utility functions and configurations
├── public/              # Static assets
└── package.json         # Project dependencies
```

## Contract Integration

The frontend integrates with the following smart contracts:

- RightsVault: `0xC2aC41FBB401B5620133Ff94606F758DbF750517`
- MusicRightsVault: `0x242a151FBEdb95Fbd8Cf06d8e382cc15753C998F`
- VerificationRegistry: `0x27150B841827Dada42cddebF1dD2cC927b3c41a1`
- EnhancedVerification: `0xceC0EF695E2f6fff4147aCB7158FF829d7351556`
- UsageTracker: `0x64C98696058AFcFa6fB75D1173b1a275fCed41C9`
- RoyaltyManager: `0x4A3531D6B3d5a2e4CcAEE26A41D1E7c88D9b2Fa5`

## Development

### Code Style

- Follow the [TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
- Use functional components with hooks
- Implement proper error handling and loading states
- Write unit tests for critical components

### Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage
```

### Building for Production

```bash
# Build the application
npm run build

# Start the production server
npm start
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 