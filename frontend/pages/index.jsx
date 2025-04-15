import { useAccount, useConnect } from 'wagmi';
import { useEffect, useState } from 'react';
import RightsManager from '../components/RightsManager';
import Layout from '../components/Layout';

export default function Home() {
  const { isConnected } = useAccount();
  const { connect, connectors, isLoading } = useConnect();
  const [mounted, setMounted] = useState(false);

  // Fix hydration issues by only rendering client-side
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  return (
    <Layout>
      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <section className="mb-12 text-center py-16">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 font-display">
            <span className="text-gradient">Music Rights Vault</span>
          </h1>
          <p className="text-xl text-mesa-gray max-w-3xl mx-auto mb-8">
            A decentralized platform for musicians to register, verify, and transfer music rights with privacy and control.
          </p>
          {!isConnected && (
            <button
              onClick={() => connect({ connector: connectors[0] })}
              disabled={!connectors[0]?.ready || isLoading}
              className="btn-mesa-primary"
            >
              Get Started
            </button>
          )}
        </section>
        
        {/* Rights Manager */}
        <section className="mb-16">
          <RightsManager />
        </section>
        
        {/* Features */}
        <section className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="mesa-card bg-white rounded-xl shadow-card p-6 border border-mesa-light-gray hover:shadow-mesa transition-all">
            <div className="w-12 h-12 mb-4 rounded-full bg-primary-50 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-2 font-display">Privacy-First</h3>
            <p className="text-mesa-gray">
              Control what information is shared with zero-knowledge proofs. Keep your rights data private.
            </p>
          </div>
          
          <div className="mesa-card bg-white rounded-xl shadow-card p-6 border border-mesa-light-gray hover:shadow-mesa transition-all">
            <div className="w-12 h-12 mb-4 rounded-full bg-primary-50 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-2 font-display">Portable Rights</h3>
            <p className="text-mesa-gray">
              Transfer your rights seamlessly between platforms and services without losing control.
            </p>
          </div>
          
          <div className="mesa-card bg-white rounded-xl shadow-card p-6 border border-mesa-light-gray hover:shadow-mesa transition-all">
            <div className="w-12 h-12 mb-4 rounded-full bg-primary-50 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-2 font-display">Verifiable Claims</h3>
            <p className="text-mesa-gray">
              Get your rights verified by trusted authorities and maintain a secure record of ownership.
            </p>
          </div>
        </section>
        
        {/* Call to Action */}
        <section className="bg-mesa-gradient rounded-2xl text-white p-10 text-center mb-16">
          <h2 className="text-3xl font-bold mb-4 font-display">Ready to secure your music rights?</h2>
          <p className="text-lg mb-8 max-w-3xl mx-auto">
            MESA Rights Vault gives you the tools to protect and manage your creative work with privacy and control.
          </p>
          {!isConnected && (
            <button
              onClick={() => connect({ connector: connectors[0] })}
              disabled={!connectors[0]?.ready || isLoading}
              className="bg-white text-primary-500 px-8 py-3 rounded-lg font-medium hover:bg-opacity-90 transition shadow-lg"
            >
              Connect Your Wallet to Begin
            </button>
          )}
        </section>
      </div>
    </Layout>
  );
} 