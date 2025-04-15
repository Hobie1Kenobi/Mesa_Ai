#!/bin/bash

# MESA Rights Vault Frontend Setup Script

# Create Next.js project with TypeScript
echo "Creating Next.js project with TypeScript..."
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

# Install Web3 dependencies
echo "Installing Web3 dependencies..."
npm install wagmi viem @tanstack/react-query zustand

# Install UI dependencies
echo "Installing UI dependencies..."
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-slot class-variance-authority clsx tailwind-merge lucide-react

# Install RainbowKit for wallet connection
echo "Installing RainbowKit..."
npm install @rainbow-me/rainbowkit

# Create environment file
echo "Creating environment file..."
cat > .env.local << EOL
NEXT_PUBLIC_RIGHTS_VAULT_CONTRACT=0xC2aC41FBB401B5620133Ff94606F758DbF750517
NEXT_PUBLIC_MUSIC_RIGHTS_VAULT_CONTRACT=0x242a151FBEdb95Fbd8Cf06d8e382cc15753C998F
NEXT_PUBLIC_VERIFICATION_REGISTRY_CONTRACT=0x27150B841827Dada42cddebF1dD2cC927b3c41a1
NEXT_PUBLIC_ENHANCED_VERIFICATION_CONTRACT=0xceC0EF695E2f6fff4147aCB7158FF829d7351556
NEXT_PUBLIC_USAGE_TRACKER_CONTRACT=0x64C98696058AFcFa6fB75D1173b1a275fCed41C9
NEXT_PUBLIC_ROYALTY_MANAGER_CONTRACT=0x4A3531D6B3d5a2e4CcAEE26A41D1E7c88D9b2Fa5
NEXT_PUBLIC_BASE_SEPOLIA_RPC=https://sepolia.base.org
EOL

# Create contract ABIs directory
echo "Creating contract ABIs directory..."
mkdir -p src/contracts/abis

# Copy contract ABIs from scripts directory
echo "Copying contract ABIs..."
cp ../scripts/*_abi.json src/contracts/abis/

# Create basic project structure
echo "Creating project structure..."
mkdir -p src/components/ui
mkdir -p src/components/contracts
mkdir -p src/hooks
mkdir -p src/lib
mkdir -p src/app/api

# Create Web3 configuration
echo "Creating Web3 configuration..."
cat > src/lib/web3.ts << EOL
import { getDefaultConfig } from '@rainbow-me/rainbowkit';
import { baseSepolia } from 'wagmi/chains';

export const config = getDefaultConfig({
  appName: 'MESA Rights Vault',
  projectId: 'YOUR_WALLETCONNECT_PROJECT_ID', // Replace with your WalletConnect project ID
  chains: [baseSepolia],
});
EOL

# Create contract configuration
echo "Creating contract configuration..."
cat > src/lib/contracts.ts << EOL
import { RightsVault__factory } from './contracts/types/factories/RightsVault__factory';
import { MusicRightsVault__factory } from './contracts/types/factories/MusicRightsVault__factory';
import { VerificationRegistry__factory } from './contracts/types/factories/VerificationRegistry__factory';
import { EnhancedVerification__factory } from './contracts/types/factories/EnhancedVerification__factory';
import { UsageTracker__factory } from './contracts/types/factories/UsageTracker__factory';
import { RoyaltyManager__factory } from './contracts/types/factories/RoyaltyManager__factory';

export const CONTRACT_ADDRESSES = {
  RIGHTS_VAULT: process.env.NEXT_PUBLIC_RIGHTS_VAULT_CONTRACT as \`0x\${string}\`,
  MUSIC_RIGHTS_VAULT: process.env.NEXT_PUBLIC_MUSIC_RIGHTS_VAULT_CONTRACT as \`0x\${string}\`,
  VERIFICATION_REGISTRY: process.env.NEXT_PUBLIC_VERIFICATION_REGISTRY_CONTRACT as \`0x\${string}\`,
  ENHANCED_VERIFICATION: process.env.NEXT_PUBLIC_ENHANCED_VERIFICATION_CONTRACT as \`0x\${string}\`,
  USAGE_TRACKER: process.env.NEXT_PUBLIC_USAGE_TRACKER_CONTRACT as \`0x\${string}\`,
  ROYALTY_MANAGER: process.env.NEXT_PUBLIC_ROYALTY_MANAGER_CONTRACT as \`0x\${string}\`,
};

export const CONTRACT_FACTORIES = {
  RIGHTS_VAULT: RightsVault__factory,
  MUSIC_RIGHTS_VAULT: MusicRightsVault__factory,
  VERIFICATION_REGISTRY: VerificationRegistry__factory,
  ENHANCED_VERIFICATION: EnhancedVerification__factory,
  USAGE_TRACKER: UsageTracker__factory,
  ROYALTY_MANAGER: RoyaltyManager__factory,
};
EOL

# Create a basic layout component
echo "Creating layout component..."
cat > src/components/layout/Layout.tsx << EOL
import React from 'react';
import { ConnectButton } from '@rainbow-me/rainbowkit';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">MESA Rights Vault</h1>
          <ConnectButton />
        </div>
      </header>
      <main>
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
};
EOL

# Create a basic home page
echo "Creating home page..."
cat > src/app/page.tsx << EOL
'use client';

import { Layout } from '@/components/layout/Layout';

export default function Home() {
  return (
    <Layout>
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:px-6">
          <h2 className="text-lg leading-6 font-medium text-gray-900">Welcome to MESA Rights Vault</h2>
          <p className="mt-1 max-w-2xl text-sm text-gray-500">Manage your music rights with privacy and security.</p>
        </div>
        <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <div className="bg-gray-50 overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg font-medium text-gray-900">Rights Management</h3>
                <p className="mt-1 text-sm text-gray-500">Register and manage your music rights.</p>
              </div>
            </div>
            <div className="bg-gray-50 overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg font-medium text-gray-900">Verification</h3>
                <p className="mt-1 text-sm text-gray-500">Verify rights ownership and status.</p>
              </div>
            </div>
            <div className="bg-gray-50 overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg font-medium text-gray-900">Royalty Management</h3>
                <p className="mt-1 text-sm text-gray-500">Track and distribute royalties.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
EOL

# Create a basic layout file
echo "Creating layout file..."
cat > src/app/layout.tsx << EOL
'use client';

import '@rainbow-me/rainbowkit/styles.css';
import './globals.css';
import { Inter } from 'next/font/google';
import { Providers } from './providers';

const inter = Inter({ subsets: ['latin'] });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
EOL

# Create providers file
echo "Creating providers file..."
cat > src/app/providers.tsx << EOL
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { WagmiProvider } from 'wagmi';
import { config } from '@/lib/web3';
import { RainbowKitProvider } from '@rainbow-me/rainbowkit';

const queryClient = new QueryClient();

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        <RainbowKitProvider>
          {children}
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  );
}
EOL

echo "Setup complete! Run 'npm run dev' to start the development server." 