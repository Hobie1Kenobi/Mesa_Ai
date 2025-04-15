import { Box, Button, Container, FormControl, FormLabel, Heading, Input, Select, Stack, Text, Textarea, VStack, useToast } from '@chakra-ui/react';
import { useState } from 'react';

export default function Register() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const toast = useToast();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    // Simulate form submission
    setTimeout(() => {
      setIsSubmitting(false);
      toast({
        title: 'Registration submitted',
        description: 'Your music rights have been registered successfully.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
    }, 2000);
  };

  return (
    <Container maxW="container.md" py={10}>
      <VStack spacing={8} align="stretch">
        <Box textAlign="center">
          <Heading as="h1" size="xl" mb={4}>
            Register Music Rights
          </Heading>
          <Text fontSize="lg" color="gray.600">
            Register and protect your AI-generated music content rights on the blockchain
          </Text>
        </Box>

        <Box as="form" onSubmit={handleSubmit} bg="white" p={8} rounded="lg" shadow="md">
          <Stack spacing={6}>
            <FormControl isRequired>
              <FormLabel>Music Title</FormLabel>
              <Input placeholder="Enter the title of your music" />
            </FormControl>

            <FormControl isRequired>
              <FormLabel>MusicBrainz ID</FormLabel>
              <Input placeholder="Enter MusicBrainz ID (if available)" />
            </FormControl>

            <FormControl isRequired>
              <FormLabel>Content Type</FormLabel>
              <Select placeholder="Select content type">
                <option value="song">Song</option>
                <option value="album">Album</option>
                <option value="remix">Remix</option>
                <option value="ai-generated">AI-Generated</option>
              </Select>
            </FormControl>

            <FormControl isRequired>
              <FormLabel>Description</FormLabel>
              <Textarea placeholder="Describe your music content" rows={4} />
            </FormControl>

            <FormControl isRequired>
              <FormLabel>Rights Type</FormLabel>
              <Select placeholder="Select rights type">
                <option value="copyright">Copyright</option>
                <option value="licensing">Licensing</option>
                <option value="distribution">Distribution</option>
                <option value="performance">Performance</option>
              </Select>
            </FormControl>

            <Button 
              type="submit" 
              colorScheme="mesa" 
              size="lg" 
              isLoading={isSubmitting}
              loadingText="Submitting"
            >
              Register Rights
            </Button>
          </Stack>
        </Box>
      </VStack>
    </Container>
  );
} 