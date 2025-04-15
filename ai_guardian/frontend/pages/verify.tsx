import { Box, Button, Container, FormControl, FormLabel, Heading, Input, Select, Stack, Text, VStack, useToast } from '@chakra-ui/react';
import { useState } from 'react';

export default function Verify() {
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<null | { status: 'success' | 'error', message: string }>(null);
  const toast = useToast();

  const handleVerify = (e: React.FormEvent) => {
    e.preventDefault();
    setIsVerifying(true);
    setVerificationResult(null);
    
    // Simulate verification process
    setTimeout(() => {
      setIsVerifying(false);
      
      // Random result for demonstration
      const isVerified = Math.random() > 0.5;
      
      if (isVerified) {
        setVerificationResult({
          status: 'success',
          message: 'The rights have been verified successfully. This content is properly registered.'
        });
        toast({
          title: 'Verification successful',
          description: 'The rights have been verified successfully.',
          status: 'success',
          duration: 5000,
          isClosable: true,
        });
      } else {
        setVerificationResult({
          status: 'error',
          message: 'The rights could not be verified. This content may not be properly registered.'
        });
        toast({
          title: 'Verification failed',
          description: 'The rights could not be verified.',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      }
    }, 2000);
  };

  return (
    <Container maxW="container.md" py={10}>
      <VStack spacing={8} align="stretch">
        <Box textAlign="center">
          <Heading as="h1" size="xl" mb={4}>
            Verify Music Rights
          </Heading>
          <Text fontSize="lg" color="gray.600">
            Verify ownership and usage rights for AI-generated music content
          </Text>
        </Box>

        <Box as="form" onSubmit={handleVerify} bg="white" p={8} rounded="lg" shadow="md">
          <Stack spacing={6}>
            <FormControl isRequired>
              <FormLabel>MusicBrainz ID</FormLabel>
              <Input placeholder="Enter MusicBrainz ID to verify" />
            </FormControl>

            <FormControl isRequired>
              <FormLabel>Verification Type</FormLabel>
              <Select placeholder="Select verification type">
                <option value="ownership">Ownership</option>
                <option value="usage">Usage Rights</option>
                <option value="licensing">Licensing</option>
                <option value="distribution">Distribution Rights</option>
              </Select>
            </FormControl>

            <Button 
              type="submit" 
              colorScheme="mesa" 
              size="lg" 
              isLoading={isVerifying}
              loadingText="Verifying"
            >
              Verify Rights
            </Button>
          </Stack>
        </Box>

        {verificationResult && (
          <Box 
            bg={verificationResult.status === 'success' ? 'green.50' : 'red.50'} 
            p={6} 
            rounded="lg" 
            borderWidth="1px" 
            borderColor={verificationResult.status === 'success' ? 'green.200' : 'red.200'}
          >
            <Text color={verificationResult.status === 'success' ? 'green.700' : 'red.700'}>
              {verificationResult.message}
            </Text>
          </Box>
        )}
      </VStack>
    </Container>
  );
} 