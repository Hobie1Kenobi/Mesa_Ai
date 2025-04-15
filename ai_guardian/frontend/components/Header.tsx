import { Box, Button, Flex, Heading, HStack, Icon, Link, Text, useColorModeValue } from '@chakra-ui/react';
import { useEffect, useState } from 'react';
import { FaWallet } from 'react-icons/fa';

export default function Header() {
  const [isConnected, setIsConnected] = useState(false);
  const [account, setAccount] = useState<string | null>(null);
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  useEffect(() => {
    checkWalletConnection();
  }, []);

  const checkWalletConnection = async () => {
    if (typeof window.ethereum !== 'undefined') {
      try {
        const accounts = await window.ethereum.request({ method: 'eth_accounts' });
        if (accounts.length > 0) {
          setIsConnected(true);
          setAccount(accounts[0]);
        }
      } catch (error) {
        console.error('Error checking wallet connection:', error);
      }
    }
  };

  const connectWallet = async () => {
    if (typeof window.ethereum !== 'undefined') {
      try {
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        setIsConnected(true);
        setAccount(accounts[0]);
      } catch (error) {
        console.error('Error connecting wallet:', error);
      }
    }
  };

  return (
    <Box as="header" bg={bgColor} borderBottom="1px" borderColor={borderColor} position="sticky" top={0} zIndex={10}>
      <Flex maxW="container.xl" mx="auto" px={4} py={4} justify="space-between" align="center">
        <HStack spacing={8}>
          <Heading size="lg" color="mesa.600" fontWeight="bold">MESA AI</Heading>
          <HStack spacing={6} display={{ base: 'none', md: 'flex' }}>
            <Link href="/" fontWeight="medium">Home</Link>
            <Link href="/register" fontWeight="medium">Register Rights</Link>
            <Link href="/verify" fontWeight="medium">Verify Rights</Link>
            <Link href="/manage" fontWeight="medium">Manage Rights</Link>
          </HStack>
        </HStack>
        <Flex align="center" gap={4}>
          {!isConnected ? (
            <Button 
              leftIcon={<Icon as={FaWallet} />} 
              onClick={connectWallet}
              variant="outline"
              size="md"
            >
              Connect Wallet
            </Button>
          ) : (
            <Button 
              leftIcon={<Icon as={FaWallet} />} 
              variant="outline"
              size="md"
            >
              {account?.slice(0, 6)}...{account?.slice(-4)}
            </Button>
          )}
        </Flex>
      </Flex>
    </Box>
  );
} 