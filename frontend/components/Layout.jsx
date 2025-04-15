import Link from 'next/link';
import { useAccount, useConnect, useDisconnect } from 'wagmi';
import { useState } from 'react';

export default function Layout({ children }) {
  const { address, isConnected } = useAccount();
  const { connect, connectors, error, isLoading, pendingConnector } = useConnect();
  const { disconnect } = useDisconnect();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#F8F9FC] flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-mesa-light-gray sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center">
            {/* Logo */}
            <Link href="/" className="flex items-center">
              <div className="mr-2 font-display font-bold text-2xl text-mesa-black">
                MESA<span className="text-mesa-blue">.</span>
              </div>
            </Link>
            <div className="ml-6 hidden md:flex space-x-6">
              <Link href="/" className="font-medium text-mesa-black hover:text-mesa-blue transition-colors">
                Rights Vault
              </Link>
              <Link href="https://mesawallet.io/about" className="font-medium text-mesa-gray hover:text-mesa-blue transition-colors">
                About
              </Link>
              <Link href="https://mesawallet.io/docs" className="font-medium text-mesa-gray hover:text-mesa-blue transition-colors">
                Docs
              </Link>
            </div>
          </div>
          
          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="text-mesa-black p-2"
            >
              {mobileMenuOpen ? (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
          
          {/* Wallet Connection */}
          <div className="hidden md:block">
            {isConnected ? (
              <div className="flex items-center space-x-4">
                <span className="text-sm bg-primary-50 text-primary-700 px-4 py-2 rounded-lg border border-primary-100">
                  {address?.slice(0, 6)}...{address?.slice(-4)}
                </span>
                <button
                  onClick={() => disconnect()}
                  className="btn-mesa-secondary"
                >
                  Disconnect
                </button>
              </div>
            ) : (
              <div>
                {connectors.map((connector) => (
                  <button
                    key={connector.id}
                    onClick={() => connect({ connector })}
                    disabled={!connector.ready || isLoading}
                    className="btn-mesa-primary"
                  >
                    {isLoading && connector.id === pendingConnector?.id
                      ? 'Connecting...'
                      : 'Connect Wallet'}
                  </button>
                ))}
                
                {error && (
                  <div className="text-red-500 text-sm mt-2">
                    {error.message}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
        
        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-mesa-light-gray bg-white">
            <div className="px-4 py-4 space-y-4">
              <Link href="/" className="block font-medium text-mesa-black hover:text-mesa-blue">
                Rights Vault
              </Link>
              <Link href="https://mesawallet.io/about" className="block font-medium text-mesa-gray hover:text-mesa-blue">
                About
              </Link>
              <Link href="https://mesawallet.io/docs" className="block font-medium text-mesa-gray hover:text-mesa-blue">
                Docs
              </Link>
              
              {/* Mobile wallet connection */}
              <div className="pt-4 border-t border-mesa-light-gray">
                {isConnected ? (
                  <div className="space-y-3">
                    <span className="text-sm bg-primary-50 text-primary-700 px-4 py-2 rounded-lg border border-primary-100 inline-block">
                      {address?.slice(0, 6)}...{address?.slice(-4)}
                    </span>
                    <button
                      onClick={() => disconnect()}
                      className="btn-mesa-secondary w-full"
                    >
                      Disconnect
                    </button>
                  </div>
                ) : (
                  <div>
                    {connectors.map((connector) => (
                      <button
                        key={connector.id}
                        onClick={() => connect({ connector })}
                        disabled={!connector.ready || isLoading}
                        className="btn-mesa-primary w-full"
                      >
                        {isLoading && connector.id === pendingConnector?.id
                          ? 'Connecting...'
                          : 'Connect Wallet'}
                      </button>
                    ))}
                    
                    {error && (
                      <div className="text-red-500 text-sm mt-2">
                        {error.message}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </header>
      
      {/* Main Content */}
      <main className="flex-grow">
        {children}
      </main>
      
      {/* Footer */}
      <footer className="bg-mesa-black text-white py-12">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-8 md:mb-0">
              <div className="font-display font-bold text-2xl mb-2">
                MESA<span className="text-mesa-blue">.</span>
              </div>
              <p className="text-mesa-gray text-sm">Privacy-First Portable Music Rights on Base</p>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-3 gap-8">
              <div>
                <h4 className="font-display font-semibold mb-4">Product</h4>
                <ul className="space-y-2">
                  <li><a href="#" className="text-mesa-gray hover:text-white transition-colors">Rights Vault</a></li>
                  <li><a href="#" className="text-mesa-gray hover:text-white transition-colors">Verification</a></li>
                  <li><a href="#" className="text-mesa-gray hover:text-white transition-colors">Privacy Tools</a></li>
                </ul>
              </div>
              <div>
                <h4 className="font-display font-semibold mb-4">Resources</h4>
                <ul className="space-y-2">
                  <li><a href="https://mesawallet.io/docs" className="text-mesa-gray hover:text-white transition-colors">Documentation</a></li>
                  <li><a href="https://github.com/mesa-wallet" className="text-mesa-gray hover:text-white transition-colors">GitHub</a></li>
                  <li><a href="#" className="text-mesa-gray hover:text-white transition-colors">FAQ</a></li>
                </ul>
              </div>
              <div>
                <h4 className="font-display font-semibold mb-4">Company</h4>
                <ul className="space-y-2">
                  <li><a href="https://mesawallet.io/about" className="text-mesa-gray hover:text-white transition-colors">About</a></li>
                  <li><a href="#" className="text-mesa-gray hover:text-white transition-colors">Privacy Policy</a></li>
                  <li><a href="#" className="text-mesa-gray hover:text-white transition-colors">Terms of Service</a></li>
                </ul>
              </div>
            </div>
          </div>
          
          <div className="mt-12 pt-8 border-t border-gray-800 text-center text-mesa-gray text-sm">
            &copy; {new Date().getFullYear()} MESA Wallet. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
} 