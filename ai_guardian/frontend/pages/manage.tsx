import { Box, Button, Container, Heading, Table, Thead, Tbody, Tr, Th, Td, Badge, HStack, IconButton, Text, VStack, useColorModeValue } from '@chakra-ui/react';
import { FaEdit, FaTrash, FaEye } from 'react-icons/fa';
import { useState } from 'react';

// Mock data for demonstration
const mockRights = [
  { id: 1, title: 'Summer Vibes', musicBrainzId: 'mb-12345', type: 'Song', rightsType: 'Copyright', status: 'Active', date: '2023-05-15' },
  { id: 2, title: 'Midnight Dreams', musicBrainzId: 'mb-67890', type: 'Album', rightsType: 'Licensing', status: 'Active', date: '2023-06-22' },
  { id: 3, title: 'AI Symphony', musicBrainzId: 'mb-24680', type: 'AI-Generated', rightsType: 'Distribution', status: 'Pending', date: '2023-07-10' },
  { id: 4, title: 'Neural Beats', musicBrainzId: 'mb-13579', type: 'Remix', rightsType: 'Performance', status: 'Active', date: '2023-08-05' },
];

export default function Manage() {
  const [rights, setRights] = useState(mockRights);
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  const handleDelete = (id: number) => {
    setRights(rights.filter(right => right.id !== id));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Active':
        return 'green';
      case 'Pending':
        return 'yellow';
      case 'Expired':
        return 'red';
      default:
        return 'gray';
    }
  };

  return (
    <Container maxW="container.xl" py={10}>
      <VStack spacing={8} align="stretch">
        <Box textAlign="center">
          <Heading as="h1" size="xl" mb={4}>
            Manage Your Rights
          </Heading>
          <Text fontSize="lg" color="gray.600">
            View and manage your registered music rights
          </Text>
        </Box>

        <Box bg={bgColor} p={6} rounded="lg" shadow="md" overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Title</Th>
                <Th>MusicBrainz ID</Th>
                <Th>Type</Th>
                <Th>Rights Type</Th>
                <Th>Status</Th>
                <Th>Date</Th>
                <Th>Actions</Th>
              </Tr>
            </Thead>
            <Tbody>
              {rights.map((right) => (
                <Tr key={right.id}>
                  <Td fontWeight="medium">{right.title}</Td>
                  <Td>{right.musicBrainzId}</Td>
                  <Td>{right.type}</Td>
                  <Td>{right.rightsType}</Td>
                  <Td>
                    <Badge colorScheme={getStatusColor(right.status)}>
                      {right.status}
                    </Badge>
                  </Td>
                  <Td>{right.date}</Td>
                  <Td>
                    <HStack spacing={2}>
                      <IconButton
                        aria-label="View details"
                        icon={<FaEye />}
                        size="sm"
                        variant="ghost"
                      />
                      <IconButton
                        aria-label="Edit rights"
                        icon={<FaEdit />}
                        size="sm"
                        variant="ghost"
                      />
                      <IconButton
                        aria-label="Delete rights"
                        icon={<FaTrash />}
                        size="sm"
                        variant="ghost"
                        colorScheme="red"
                        onClick={() => handleDelete(right.id)}
                      />
                    </HStack>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>

        <Box textAlign="center">
          <Button colorScheme="mesa" size="lg">
            Register New Rights
          </Button>
        </Box>
      </VStack>
    </Container>
  );
} 