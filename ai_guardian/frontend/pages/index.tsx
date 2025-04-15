import { Box, Button, Container, Flex, Grid, Heading, Icon, Image, Link, SimpleGrid, Stack, Text, VStack, useColorModeValue } from '@chakra-ui/react';
import { FaCheckCircle, FaLock, FaShieldAlt, FaWallet } from 'react-icons/fa';
import { useEffect, useState } from 'react';

export default function Home() {
  const [isConnected, setIsConnected] = useState(false);
  const [account, setAccount] = useState<string | null>(null);
  const bgColor = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.600', 'gray.300');

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

  return (
    <Box>
      {/* Hero Section */}
      <Box bg="mesa.50" py={20}>
        <Container maxW="container.xl">
          <Grid templateColumns={{ base: '1fr', md: '1fr 1fr' }} gap={10} alignItems="center">
            <VStack align="start" spacing={6}>
              <Heading as="h1" size="2xl" color="mesa.700">
                MESA AI - Music Rights Oracle
              </Heading>
              <Text fontSize="xl" color={textColor}>
                Secure and transparent rights management for AI-generated content on the blockchain
              </Text>
              <Stack direction={{ base: 'column', sm: 'row' }} spacing={4}>
                <Button size="lg" colorScheme="mesa" isDisabled={!isConnected}>
                  Register New Content
                </Button>
                <Button size="lg" variant="outline" colorScheme="mesa" isDisabled={!isConnected}>
                  Learn More
                </Button>
              </Stack>
            </VStack>
            <Box>
              <Image 
                src="/hero-image.png" 
                alt="MESA AI Music Rights" 
                fallbackSrc="https://via.placeholder.com/600x400?text=MESA+AI+Music+Rights"
                borderRadius="lg"
                shadow="xl"
              />
            </Box>
          </Grid>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxW="container.xl" py={20}>
        <VStack spacing={12}>
          <Box textAlign="center">
            <Heading as="h2" size="xl" mb={4}>
              Key Features
            </Heading>
            <Text fontSize="lg" color={textColor} maxW="2xl" mx="auto">
              Our platform provides comprehensive tools for managing music rights in the AI era
            </Text>
          </Box>

          <SimpleGrid columns={{ base: 1, md: 3 }} spacing={10} width="100%">
            <FeatureCard 
              icon={FaShieldAlt} 
              title="Secure Rights Registration" 
              description="Register and protect your AI-generated content rights on the blockchain with advanced encryption"
            />
            <FeatureCard 
              icon={FaCheckCircle} 
              title="Verification System" 
              description="Verify ownership and usage rights for AI-generated content with zero-knowledge proofs"
            />
            <FeatureCard 
              icon={FaLock} 
              title="Privacy Controls" 
              description="Control what data is public and what remains private with selective disclosure"
            />
          </SimpleGrid>
        </VStack>
      </Container>

      {/* CTA Section */}
      <Box bg="mesa.600" color="white" py={16}>
        <Container maxW="container.xl">
          <Flex direction={{ base: 'column', md: 'row' }} justify="space-between" align="center">
            <Box mb={{ base: 6, md: 0 }}>
              <Heading as="h2" size="xl" mb={2}>
                Ready to protect your music rights?
              </Heading>
              <Text fontSize="lg">
                Connect your wallet and start managing your rights today
              </Text>
            </Box>
            <Button 
              size="lg" 
              bg="white" 
              color="mesa.600" 
              _hover={{ bg: 'gray.100' }}
              isDisabled={!isConnected}
            >
              Get Started
            </Button>
          </Flex>
        </Container>
      </Box>
    </Box>
  );
}

// Feature card component
function FeatureCard({ icon, title, description }: { icon: any, title: string, description: string }) {
  const bgColor = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.600', 'gray.300');
  
  return (
    <Box bg={bgColor} p={6} rounded="lg" shadow="md" height="100%">
      <Icon as={icon} w={10} h={10} color="mesa.500" mb={4} />
      <Heading as="h3" size="md" mb={3}>
        {title}
      </Heading>
      <Text color={textColor}>
        {description}
      </Text>
    </Box>
  );
} 