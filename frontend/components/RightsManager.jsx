import { useState, useEffect } from 'react';
import { useAccount, useContractRead, useContractWrite, useContract } from 'wagmi';
import { ethers } from 'ethers';

// ABI imports would come from contract artifacts
import MusicRightsVaultABI from '../../artifacts/contracts/MusicRightsVault.sol/MusicRightsVault.json';
import VerificationRegistryABI from '../../artifacts/contracts/VerificationRegistry.sol/VerificationRegistry.json';

const MUSIC_RIGHTS_VAULT_ADDRESS = process.env.NEXT_PUBLIC_MUSIC_RIGHTS_VAULT_ADDRESS;
const VERIFICATION_REGISTRY_ADDRESS = process.env.NEXT_PUBLIC_VERIFICATION_REGISTRY_ADDRESS;

export default function RightsManager() {
  const { address, isConnected } = useAccount();
  const [rightName, setRightName] = useState('');
  const [rightDescription, setRightDescription] = useState('');
  const [rightMetadata, setRightMetadata] = useState({});
  const [selectedRightId, setSelectedRightId] = useState('');
  const [transferTo, setTransferTo] = useState('');
  const [activeTab, setActiveTab] = useState('register'); // 'register', 'view', 'transfer'
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [notification, setNotification] = useState({ show: false, message: '', type: '' });
  
  // Read user's rights
  const { data: userRights, isLoading: rightsLoading, refetch: refetchRights } = useContractRead({
    address: MUSIC_RIGHTS_VAULT_ADDRESS,
    abi: MusicRightsVaultABI.abi,
    functionName: 'getMyRights',
    args: [],
    enabled: isConnected,
  });
  
  // Contract interactions
  const { write: registerRight, isLoading: isRegistering } = useContractWrite({
    address: MUSIC_RIGHTS_VAULT_ADDRESS,
    abi: MusicRightsVaultABI.abi,
    functionName: 'registerRight',
    onSuccess: () => {
      showNotification('Right registered successfully!', 'success');
      setRightName('');
      setRightDescription('');
      setTimeout(() => refetchRights(), 2000);
    },
    onError: (error) => {
      showNotification('Error registering right: ' + error.message, 'error');
    }
  });
  
  const { write: transferRight, isLoading: isTransferring } = useContractWrite({
    address: MUSIC_RIGHTS_VAULT_ADDRESS,
    abi: MusicRightsVaultABI.abi,
    functionName: 'transferRight',
    onSuccess: () => {
      showNotification('Right transferred successfully!', 'success');
      setSelectedRightId('');
      setTransferTo('');
      setTimeout(() => refetchRights(), 2000);
    },
    onError: (error) => {
      showNotification('Error transferring right: ' + error.message, 'error');
    }
  });

  const showNotification = (message, type) => {
    setNotification({ show: true, message, type });
    setTimeout(() => setNotification({ show: false, message: '', type: '' }), 5000);
  };
  
  // Handle right registration
  const handleRegisterRight = async () => {
    if (!rightName || !rightDescription) return;
    
    try {
      setIsSubmitting(true);
      
      // Create metadata
      const metadata = {
        name: rightName,
        description: rightDescription,
        createdAt: new Date().toISOString(),
        owner: address,
      };
      
      // In a real app, this would be stored off-chain (IPFS, etc.)
      // and only the hash would be stored on-chain
      const metadataHash = ethers.utils.id(JSON.stringify(metadata));
      
      // Generate a unique ID for the right
      const rightId = ethers.utils.id(`${address}-${Date.now()}`);
      
      // Register the right on-chain
      await registerRight({
        args: [rightId, metadataHash],
      });
    } catch (error) {
      console.error('Error registering right:', error);
      showNotification('Error registering right', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Handle right transfer
  const handleTransferRight = async () => {
    if (!selectedRightId || !ethers.utils.isAddress(transferTo)) return;
    
    try {
      setIsSubmitting(true);
      
      await transferRight({
        args: [selectedRightId, transferTo],
      });
    } catch (error) {
      console.error('Error transferring right:', error);
      showNotification('Error transferring right', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Fetch metadata for a right ID
  const fetchRightMetadata = async (rightId) => {
    try {
      const metadataHash = await readContract({
        address: MUSIC_RIGHTS_VAULT_ADDRESS,
        abi: MusicRightsVaultABI.abi,
        functionName: 'getRightMetadataHash',
        args: [rightId],
      });
      
      // In a real app, you would fetch the actual metadata from IPFS or similar
      // Here we're simulating by using a placeholder
      setRightMetadata({
        ...rightMetadata,
        [rightId]: {
          id: rightId,
          name: `Right ${rightId.slice(0, 6)}`,
          hash: metadataHash,
        },
      });
    } catch (error) {
      console.error(`Error fetching metadata for ${rightId}:`, error);
    }
  };
  
  // Fetch metadata for all rights
  useEffect(() => {
    if (userRights && userRights.length > 0) {
      userRights.forEach(rightId => {
        fetchRightMetadata(rightId);
      });
    }
  }, [userRights]);
  
  if (!isConnected) {
    return (
      <div className="mesa-card flex flex-col items-center py-12 bg-white rounded-2xl shadow-card border border-mesa-light-gray">
        <div className="w-16 h-16 mb-6 rounded-full bg-primary-50 flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        <h2 className="text-2xl font-bold text-center mb-4 font-display">Music Rights Manager</h2>
        <p className="text-mesa-gray text-center mb-8 max-w-md">
          Connect your wallet to manage your music rights securely on the Base network.
        </p>
        <div className="w-40 h-1 bg-primary-100 rounded-full"></div>
      </div>
    );
  }
  
  return (
    <div className="mesa-card bg-white rounded-2xl shadow-card border border-mesa-light-gray p-8">
      <h2 className="text-3xl font-bold mb-8 text-center font-display">
        <span className="text-gradient">Music Rights Manager</span>
      </h2>
      
      {/* Notification */}
      {notification.show && (
        <div className={`mb-6 p-4 rounded-lg ${notification.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
          {notification.message}
        </div>
      )}
      
      {/* Tabs */}
      <div className="mb-8 border-b border-mesa-light-gray">
        <div className="flex flex-wrap md:flex-nowrap space-x-2 md:space-x-8">
          <button
            onClick={() => setActiveTab('register')}
            className={`pb-4 px-2 font-medium transition-colors ${activeTab === 'register' ? 'text-primary-500 border-b-2 border-primary-500' : 'text-mesa-gray hover:text-primary-400'}`}
          >
            Register New Right
          </button>
          <button
            onClick={() => setActiveTab('view')}
            className={`pb-4 px-2 font-medium transition-colors ${activeTab === 'view' ? 'text-primary-500 border-b-2 border-primary-500' : 'text-mesa-gray hover:text-primary-400'}`}
          >
            My Rights
          </button>
          <button
            onClick={() => setActiveTab('transfer')}
            className={`pb-4 px-2 font-medium transition-colors ${activeTab === 'transfer' ? 'text-primary-500 border-b-2 border-primary-500' : 'text-mesa-gray hover:text-primary-400'}`}
          >
            Transfer Right
          </button>
        </div>
      </div>
      
      {/* Register New Right */}
      {activeTab === 'register' && (
        <div className="py-4">
          <div className="mb-6">
            <label className="block text-sm font-medium text-mesa-black mb-2">
              Right Name
            </label>
            <input
              type="text"
              value={rightName}
              onChange={(e) => setRightName(e.target.value)}
              className="mesa-input w-full border border-mesa-light-gray rounded-lg px-4 py-3 focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
              placeholder="e.g., Song Title - Composition Rights"
            />
          </div>
          <div className="mb-8">
            <label className="block text-sm font-medium text-mesa-black mb-2">
              Description
            </label>
            <textarea
              value={rightDescription}
              onChange={(e) => setRightDescription(e.target.value)}
              className="mesa-input w-full border border-mesa-light-gray rounded-lg px-4 py-3 focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
              rows="4"
              placeholder="Describe the rights you're registering"
            />
          </div>
          <button
            onClick={handleRegisterRight}
            disabled={isRegistering || isSubmitting || !rightName || !rightDescription}
            className={`btn-mesa-primary w-full flex justify-center items-center ${(isRegistering || isSubmitting) ? 'opacity-70 cursor-not-allowed' : ''}`}
          >
            {(isRegistering || isSubmitting) ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Registering...
              </>
            ) : 'Register Right'}
          </button>
        </div>
      )}
      
      {/* My Rights */}
      {activeTab === 'view' && (
        <div className="py-4">
          {rightsLoading ? (
            <div className="text-center py-12">
              <div className="w-12 h-12 border-4 border-primary-200 border-t-primary-500 rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-mesa-gray">Loading your rights...</p>
            </div>
          ) : userRights && userRights.length > 0 ? (
            <div className="space-y-4">
              {userRights.map((rightId) => (
                <div key={rightId} className="p-6 border border-mesa-light-gray rounded-xl flex flex-col md:flex-row justify-between md:items-center gap-4 hover:border-primary-300 hover:shadow-sm transition-all">
                  <div>
                    <p className="font-semibold text-mesa-black text-lg">
                      {rightMetadata[rightId]?.name || `Right ${rightId.slice(0, 6)}...${rightId.slice(-4)}`}
                    </p>
                    <p className="text-sm text-mesa-gray font-mono mt-1">ID: {rightId.slice(0, 10)}...{rightId.slice(-8)}</p>
                  </div>
                  <div className="flex space-x-3">
                    <button
                      onClick={() => {
                        setSelectedRightId(rightId);
                        setActiveTab('transfer');
                      }}
                      className="px-4 py-2 bg-primary-50 text-primary-700 font-medium rounded-lg hover:bg-primary-100 transition-colors"
                    >
                      Transfer
                    </button>
                    <button
                      onClick={() => setSelectedRightId(rightId)}
                      className="px-4 py-2 bg-gray-100 text-mesa-gray font-medium rounded-lg hover:bg-gray-200 transition-colors"
                    >
                      Details
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 px-4">
              <div className="w-20 h-20 mb-6 rounded-full bg-gray-100 flex items-center justify-center mx-auto">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-mesa-gray" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-display font-semibold mb-2">No Rights Found</h3>
              <p className="text-mesa-gray mb-6 max-w-md mx-auto">You don't have any registered rights yet. Create your first right to get started.</p>
              <button 
                onClick={() => setActiveTab('register')}
                className="btn-mesa-primary"
              >
                Register Your First Right
              </button>
            </div>
          )}
        </div>
      )}
      
      {/* Transfer Right */}
      {activeTab === 'transfer' && (
        <div className="py-4">
          <div className="mb-8">
            <label className="block text-sm font-medium text-mesa-black mb-2">
              Selected Right
            </label>
            {selectedRightId ? (
              <div className="p-6 border border-primary-200 bg-primary-50 rounded-xl mb-4">
                <p className="font-semibold text-mesa-black text-lg">
                  {rightMetadata[selectedRightId]?.name || `Right ${selectedRightId.slice(0, 6)}...${selectedRightId.slice(-4)}`}
                </p>
                <p className="text-sm text-mesa-gray font-mono mt-1">ID: {selectedRightId.slice(0, 10)}...{selectedRightId.slice(-8)}</p>
              </div>
            ) : (
              <div className="p-6 border border-mesa-light-gray bg-gray-50 rounded-xl mb-4 text-center">
                <p className="text-mesa-gray">No right selected</p>
                <p className="text-sm text-mesa-gray mt-1">Please select a right from the "My Rights" tab</p>
              </div>
            )}
            {!selectedRightId && (
              <button
                onClick={() => setActiveTab('view')}
                className="w-full btn-mesa-secondary mt-4"
              >
                Go to My Rights
              </button>
            )}
          </div>
          
          {selectedRightId && (
            <>
              <div className="mb-8">
                <label className="block text-sm font-medium text-mesa-black mb-2">
                  Recipient Address
                </label>
                <input
                  type="text"
                  value={transferTo}
                  onChange={(e) => setTransferTo(e.target.value)}
                  className="mesa-input w-full border border-mesa-light-gray rounded-lg px-4 py-3 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 font-mono"
                  placeholder="0x..."
                />
                <p className="mt-2 text-xs text-mesa-gray">Enter the wallet address of the recipient who will receive this right.</p>
              </div>
              <button
                onClick={handleTransferRight}
                disabled={isTransferring || isSubmitting || !selectedRightId || !transferTo || !ethers.utils.isAddress(transferTo)}
                className={`btn-mesa-primary w-full flex justify-center items-center ${(isTransferring || isSubmitting) ? 'opacity-70 cursor-not-allowed' : ''}`}
              >
                {(isTransferring || isSubmitting) ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Transferring...
                  </>
                ) : 'Transfer Right'}
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
} 