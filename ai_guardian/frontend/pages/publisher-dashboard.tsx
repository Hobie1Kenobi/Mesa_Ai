import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Container,
  Flex,
  Heading,
  SimpleGrid,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Tag,
  Text,
  Progress,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  HStack,
  VStack,
  Icon,
  Input,
  useToast,
  Badge,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Select,
  Card,
  CardHeader,
  CardBody,
  Divider,
  IconButton,
  useDisclosure
} from '@chakra-ui/react';
import { FiUploadCloud, FiCheck, FiAlertCircle, FiFilter, FiDownload, FiMoreVertical, FiSearch, FiChevronDown, FiRefreshCw, FiFileText, FiDatabase, FiBarChart2 } from 'react-icons/fi';
// Import the new visualization component
import FloatingBubbleChart from '../components/FloatingBubbleChart';
// Import the catalog import modal
import ImportCatalogModal from '../components/ImportCatalogModal';
// Import the publisher profile component
import PublisherProfile from '../components/PublisherProfile';

// Sample imported catalog data (would normally come from API/backend)
const sampleCatalog = [
  {
    id: 1,
    title: 'Midnight Dreams',
    artist: 'Sophia Chen',
    isrc: 'USRC78901234',
    iswc: 'T-345.678.910-2',
    year: 2022,
    status: 'registered',
    rightsId: '0x8b4c...e721',
    txHash: '0x5e73...f982',
    timestamp: '2023-06-15T14:23:45Z',
    publisher: 'Evergreen Music Publishing'
  },
  {
    id: 2,
    title: 'Ocean Breeze',
    artist: 'The Wavelengths',
    isrc: 'USRC45678901',
    iswc: 'T-987.654.321-0',
    year: 2020,
    status: 'registered',
    rightsId: '0x2a7d...9c45',
    txHash: '0xd82f...1a4c',
    timestamp: '2023-06-15T14:24:12Z',
    publisher: 'Evergreen Music Publishing'
  },
  {
    id: 3,
    title: 'Skyward',
    artist: 'Marcus Lee',
    isrc: 'USRC56789012',
    iswc: 'T-456.789.123-4',
    year: 2023,
    status: 'pending',
    rightsId: '0x9f3b...0d67',
    txHash: null,
    timestamp: null,
    publisher: 'Evergreen Music Publishing'
  },
  {
    id: 4,
    title: 'Autumn Leaves Fall',
    artist: 'The Seasons',
    isrc: 'USRC34567890',
    iswc: 'T-654.321.987-6',
    year: 2018,
    status: 'failed',
    rightsId: null,
    txHash: null,
    timestamp: null,
    publisher: 'Evergreen Music Publishing',
    error: 'Duplicate rights ID'
  },
  {
    id: 5,
    title: 'City Lights',
    artist: 'Urban Noise Collective',
    isrc: 'USRC23456789',
    iswc: 'T-789.123.456-8',
    year: 2021,
    status: 'registered',
    rightsId: '0x3c8e...f547',
    txHash: '0x7b2a...9d34',
    timestamp: '2023-06-15T14:26:01Z',
    publisher: 'Evergreen Music Publishing'
  }
];

// Define status badges with colors
const StatusBadge = ({ status }: { status: string }) => {
  let color = 'gray';
  
  switch (status) {
    case 'registered':
      color = 'green';
      break;
    case 'pending':
      color = 'orange';
      break;
    case 'failed':
      color = 'red';
      break;
    default:
      color = 'gray';
  }
  
  return <Badge colorScheme={color}>{status}</Badge>;
};

export default function PublisherDashboard() {
  const [catalog, setCatalog] = useState(sampleCatalog);
  const [isImporting, setIsImporting] = useState(false);
  const [importProgress, setImportProgress] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  // Filter the catalog based on search term and status filter
  const filteredCatalog = catalog.filter(item => {
    const matchesSearch = 
      item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.artist.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.isrc.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || item.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });
  
  // Stats for dashboard
  const stats = {
    total: catalog.length,
    registered: catalog.filter(item => item.status === 'registered').length,
    pending: catalog.filter(item => item.status === 'pending').length,
    failed: catalog.filter(item => item.status === 'failed').length,
  };
  
  // Modified for real CSV import
  const handleImport = () => {
    onOpen(); // Open the import modal instead of using mock import
  };

  // Handle imported data from the modal
  const handleImportComplete = (importedData: any[]) => {
    // Add the imported data to the catalog
    setCatalog(prev => [...prev, ...importedData]);
    
    // Show a notification about successful import
    toast({
      title: 'Import complete',
      description: `Successfully imported ${importedData.length} tracks`,
      status: 'success',
      duration: 5000,
      isClosable: true,
    });
  };
  
  return (
    <Box minH="100vh" bg="gray.50">
      <Container maxW="container.xl" py={8}>
        <Flex justifyContent="space-between" alignItems="center" mb={8}>
          <Heading size="xl">Publisher Dashboard</Heading>
          <Button 
            colorScheme="blue" 
            leftIcon={<FiUploadCloud />}
            onClick={handleImport}
          >
            Import Catalog
          </Button>
        </Flex>
        
        {/* Import Modal */}
        <ImportCatalogModal 
          isOpen={isOpen} 
          onClose={onClose} 
          onImportComplete={handleImportComplete} 
        />
        
        {/* Publisher Profile */}
        <Box mb={8}>
          <PublisherProfile 
            publisherName="Evergreen Music Publishing" 
            catalog={catalog} 
          />
        </Box>
        
        {/* Stats Cards */}
        <SimpleGrid columns={{ base: 1, md: 4 }} spacing={6} mb={8}>
          <Card>
            <CardBody>
              <Stat>
                <StatLabel>Total Tracks</StatLabel>
                <StatNumber>{stats.total}</StatNumber>
                <StatHelpText>In your catalog</StatHelpText>
              </Stat>
            </CardBody>
          </Card>
          
          <Card>
            <CardBody>
              <Stat>
                <StatLabel>Registered</StatLabel>
                <StatNumber>{stats.registered}</StatNumber>
                <StatHelpText color="green.500">
                  <FiCheck /> On blockchain
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>
          
          <Card>
            <CardBody>
              <Stat>
                <StatLabel>Pending</StatLabel>
                <StatNumber>{stats.pending}</StatNumber>
                <StatHelpText color="orange.500">
                  Awaiting confirmation
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>
          
          <Card>
            <CardBody>
              <Stat>
                <StatLabel>Failed</StatLabel>
                <StatNumber>{stats.failed}</StatNumber>
                <StatHelpText color="red.500">
                  <FiAlertCircle /> Need attention
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>
        </SimpleGrid>
        
        {/* Import Progress */}
        {isImporting && (
          <Box mb={8} bg="white" p={4} borderRadius="md" boxShadow="sm">
            <Text mb={2}>Importing catalog...</Text>
            <Progress value={importProgress} size="sm" colorScheme="blue" />
          </Box>
        )}
        
        {/* Tabs for different views */}
        <Tabs variant="enclosed" colorScheme="blue">
          <TabList>
            <Tab><Icon as={FiDatabase} mr={2} /> Catalog</Tab>
            <Tab><Icon as={FiBarChart2} mr={2} /> Analytics</Tab>
            <Tab><Icon as={FiFileText} mr={2} /> Reports</Tab>
          </TabList>
          
          <TabPanels>
            <TabPanel p={0} pt={4}>
              {/* Search and Filter */}
              <Flex mb={4} gap={4} direction={{ base: 'column', md: 'row' }}>
                <Box flex={1}>
                  <Input 
                    placeholder="Search by title, artist or ISRC..." 
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    leftIcon={<FiSearch />}
                  />
                </Box>
                <Box w={{ base: 'full', md: '200px' }}>
                  <Select 
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                  >
                    <option value="all">All Statuses</option>
                    <option value="registered">Registered</option>
                    <option value="pending">Pending</option>
                    <option value="failed">Failed</option>
                  </Select>
                </Box>
                <IconButton
                  aria-label="Refresh"
                  icon={<FiRefreshCw />}
                  onClick={() => {
                    // In a real app, this would refresh data from the API
                    toast({
                      title: 'Refreshed',
                      status: 'info',
                      duration: 2000,
                    });
                  }}
                />
                <Menu>
                  <MenuButton as={Button} rightIcon={<FiChevronDown />}>
                    Export
                  </MenuButton>
                  <MenuList>
                    <MenuItem icon={<FiDownload />}>Export as CSV</MenuItem>
                    <MenuItem icon={<FiDownload />}>Export as Excel</MenuItem>
                    <MenuItem icon={<FiDownload />}>Export Blockchain Data</MenuItem>
                  </MenuList>
                </Menu>
              </Flex>
              
              {/* Catalog Table */}
              <Box overflowX="auto" bg="white" borderRadius="md" boxShadow="sm">
                <Table variant="simple">
                  <Thead bg="gray.50">
                    <Tr>
                      <Th>Title</Th>
                      <Th>Artist</Th>
                      <Th>ISRC</Th>
                      <Th>Year</Th>
                      <Th>Status</Th>
                      <Th>Rights ID</Th>
                      <Th>Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {filteredCatalog.map((item) => (
                      <Tr key={item.id}>
                        <Td fontWeight="medium">{item.title}</Td>
                        <Td>{item.artist}</Td>
                        <Td>
                          <Text fontFamily="mono" fontSize="sm">
                            {item.isrc}
                          </Text>
                        </Td>
                        <Td>{item.year}</Td>
                        <Td>
                          <StatusBadge status={item.status} />
                        </Td>
                        <Td>
                          {item.rightsId ? (
                            <Text fontFamily="mono" fontSize="sm">
                              {item.rightsId}
                            </Text>
                          ) : (
                            <Text color="gray.400">-</Text>
                          )}
                        </Td>
                        <Td>
                          <Menu>
                            <MenuButton
                              as={IconButton}
                              aria-label="Options"
                              icon={<FiMoreVertical />}
                              variant="ghost"
                              size="sm"
                            />
                            <MenuList>
                              <MenuItem>View Details</MenuItem>
                              <MenuItem>View on BaseScan</MenuItem>
                              <MenuItem>Edit Metadata</MenuItem>
                              <MenuItem>Manage Royalties</MenuItem>
                              {item.status === 'failed' && (
                                <MenuItem color="red.500">Retry Registration</MenuItem>
                              )}
                            </MenuList>
                          </Menu>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </Box>
              
              {filteredCatalog.length === 0 && (
                <Box textAlign="center" py={10}>
                  <Text color="gray.500">No tracks found matching your filters</Text>
                </Box>
              )}
            </TabPanel>
            
            <TabPanel>
              <Box p={6} bg="white" borderRadius="md" boxShadow="sm">
                <Heading size="md" mb={4}>Analytics Dashboard</Heading>
                
                <Text mb={6}>Interactive visualization of your music catalog with registration status and details.</Text>
                
                {/* 3D Floating Bubble Visualization */}
                <Box h="600px" mb={6}>
                  <FloatingBubbleChart data={filteredCatalog} />
                </Box>
                
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={5} mt={8}>
                  <Box p={4} bg="gray.50" borderRadius="md">
                    <Heading size="sm" mb={3}>Registration Metrics</Heading>
                    <Text>Registration metrics and blockchain-related statistics would appear here.</Text>
                  </Box>
                  <Box p={4} bg="gray.50" borderRadius="md">
                    <Heading size="sm" mb={3}>Gas Usage Analysis</Heading>
                    <Text>Gas usage trends and optimization recommendations would appear here.</Text>
                  </Box>
                </SimpleGrid>
              </Box>
            </TabPanel>
            
            <TabPanel>
              <Box p={6} bg="white" borderRadius="md" boxShadow="sm">
                <Heading size="md" mb={4}>Reports</Heading>
                <Text>Generated reports and blockchain verification documents would be available here.</Text>
              </Box>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </Container>
    </Box>
  );
} 