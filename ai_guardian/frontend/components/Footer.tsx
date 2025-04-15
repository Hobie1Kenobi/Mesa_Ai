import { Box, Container, Flex, Grid, Heading, Icon, Link, Stack, Text, useColorModeValue } from '@chakra-ui/react';
import { FaGithub, FaTwitter, FaDiscord } from 'react-icons/fa';

export default function Footer() {
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.600', 'gray.400');

  return (
    <Box as="footer" bg={bgColor} borderTop="1px" borderColor={borderColor} py={10}>
      <Container maxW="container.xl">
        <Grid templateColumns={{ base: '1fr', md: '2fr 1fr 1fr 1fr' }} gap={8}>
          <Box>
            <Heading size="md" color="mesa.600" mb={4}>MESA AI</Heading>
            <Text color={textColor} mb={4}>
              Secure and transparent rights management for AI-generated content on the blockchain
            </Text>
            <Stack direction="row" spacing={4}>
              <Link href="https://twitter.com" isExternal>
                <Icon as={FaTwitter} w={5} h={5} />
              </Link>
              <Link href="https://github.com" isExternal>
                <Icon as={FaGithub} w={5} h={5} />
              </Link>
              <Link href="https://discord.com" isExternal>
                <Icon as={FaDiscord} w={5} h={5} />
              </Link>
            </Stack>
          </Box>
          
          <Box>
            <Heading as="h3" size="sm" mb={4}>Product</Heading>
            <Stack spacing={2}>
              <Link href="/register">Register Rights</Link>
              <Link href="/verify">Verify Rights</Link>
              <Link href="/manage">Manage Rights</Link>
              <Link href="/pricing">Pricing</Link>
            </Stack>
          </Box>
          
          <Box>
            <Heading as="h3" size="sm" mb={4}>Resources</Heading>
            <Stack spacing={2}>
              <Link href="/docs">Documentation</Link>
              <Link href="/api">API</Link>
              <Link href="/blog">Blog</Link>
              <Link href="/faq">FAQ</Link>
            </Stack>
          </Box>
          
          <Box>
            <Heading as="h3" size="sm" mb={4}>Company</Heading>
            <Stack spacing={2}>
              <Link href="/about">About</Link>
              <Link href="/team">Team</Link>
              <Link href="/careers">Careers</Link>
              <Link href="/contact">Contact</Link>
            </Stack>
          </Box>
        </Grid>
        
        <Flex 
          direction={{ base: 'column', md: 'row' }} 
          justify="space-between" 
          align="center" 
          pt={8} 
          mt={8} 
          borderTop="1px" 
          borderColor={borderColor}
        >
          <Text color={textColor} fontSize="sm">
            © {new Date().getFullYear()} MESA AI. All rights reserved.
          </Text>
          <Stack direction="row" spacing={6} mt={{ base: 4, md: 0 }}>
            <Link href="/privacy" fontSize="sm">Privacy Policy</Link>
            <Link href="/terms" fontSize="sm">Terms of Service</Link>
          </Stack>
        </Flex>
      </Container>
    </Box>
  );
} 