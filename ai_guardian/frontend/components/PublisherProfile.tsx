import React, { useState, useEffect } from 'react';
import {
  Box,
  Flex,
  Text,
  Heading,
  VStack,
  HStack,
  Divider,
  Badge,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Grid,
  GridItem,
  Image,
  Icon,
  Button,
  useColorModeValue,
  Tooltip,
  Progress
} from '@chakra-ui/react';
import { FiCheck, FiInfo, FiLock, FiDollarSign, FiBarChart2, FiFileText, FiUsers } from 'react-icons/fi';

interface PublisherProfileProps {
  publisherName: string;
  catalog: any[];
}

export default function PublisherProfile({ publisherName, catalog }: PublisherProfileProps) {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const accentColor = useColorModeValue('blue.500', 'blue.300');
  
  // Calculate stats based on catalog
  const registered = catalog.filter(item => item.status === 'registered').length;
  const pending = catalog.filter(item => item.status === 'pending').length;
  const failed = catalog.filter(item => item.status === 'failed').length;
  const registrationRate = catalog.length > 0 ? (registered / catalog.length) * 100 : 0;
  
  // Generate random usage stats for demo purposes
  const [usageStats, setUsageStats] = useState({
    totalUsage: 0,
    weeklyPlays: 0,
    monthlyListeners: 0,
    averageRoyalty: 0
  });
  
  useEffect(() => {
    // Simulate loading usage data
    setUsageStats({
      totalUsage: Math.floor(registered * 1250 + Math.random() * 5000),
      weeklyPlays: Math.floor(registered * 230 + Math.random() * 1000),
      monthlyListeners: Math.floor(registered * 85 + Math.random() * 500),
      averageRoyalty: parseFloat((0.004 + Math.random() * 0.002).toFixed(4))
    });
  }, [registered]);
  
  return (
    <Box 
      bg={bgColor} 
      p={6} 
      borderRadius="lg" 
      boxShadow="md"
      border="1px"
      borderColor={borderColor}
    >
      {/* Publisher Header */}
      <Flex 
        direction={{ base: 'column', md: 'row' }} 
        align={{ base: 'start', md: 'center' }} 
        justify="space-between"
        mb={6}
      >
        <VStack align="start" spacing={1}>
          <Heading size="lg" color={accentColor}>{publisherName}</Heading>
          <Text color="gray.600">Verified Music Rights Publisher</Text>
          <HStack mt={2}>
            <Badge colorScheme="green">Verified</Badge>
            <Badge colorScheme="blue">Premium Account</Badge>
            <Badge colorScheme="purple">Blockchain Secured</Badge>
          </HStack>
        </VStack>
        
        <HStack spacing={4} mt={{ base: 4, md: 0 }}>
          <Button size="sm" leftIcon={<FiFileText />} colorScheme="gray">View Reports</Button>
          <Button size="sm" leftIcon={<FiUsers />} colorScheme="blue">Manage Team</Button>
        </HStack>
      </Flex>
      
      <Divider mb={6} />
      
      {/* Stats Grid */}
      <Grid 
        templateColumns={{ base: 'repeat(1, 1fr)', md: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' }} 
        gap={4}
        mb={6}
      >
        <GridItem>
          <Stat 
            bg="gray.50" 
            p={4} 
            borderRadius="md" 
            borderLeft="4px" 
            borderLeftColor={accentColor}
          >
            <StatLabel>Catalog Size</StatLabel>
            <StatNumber>{catalog.length}</StatNumber>
            <StatHelpText>Total Tracks</StatHelpText>
          </Stat>
        </GridItem>
        
        <GridItem>
          <Stat 
            bg="gray.50" 
            p={4} 
            borderRadius="md" 
            borderLeft="4px" 
            borderLeftColor="green.500"
          >
            <StatLabel>Registration Rate</StatLabel>
            <StatNumber>{registrationRate.toFixed(1)}%</StatNumber>
            <StatHelpText>
              <Progress 
                value={registrationRate} 
                size="xs" 
                colorScheme="green" 
                mt={1}
              />
            </StatHelpText>
          </Stat>
        </GridItem>
        
        <GridItem>
          <Stat 
            bg="gray.50" 
            p={4} 
            borderRadius="md" 
            borderLeft="4px" 
            borderLeftColor="purple.500"
          >
            <StatLabel>Blockchain Status</StatLabel>
            <StatNumber>{registered} / {catalog.length}</StatNumber>
            <StatHelpText>
              <HStack spacing={2}>
                <Icon as={FiCheck} color="green.500" />
                <Text>Verified on chain</Text>
              </HStack>
            </StatHelpText>
          </Stat>
        </GridItem>
        
        <GridItem>
          <Stat 
            bg="gray.50" 
            p={4} 
            borderRadius="md" 
            borderLeft="4px" 
            borderLeftColor="orange.500"
          >
            <StatLabel>Average Gas Cost</StatLabel>
            <StatNumber>0.0012 ETH</StatNumber>
            <StatHelpText>Per registration</StatHelpText>
          </Stat>
        </GridItem>
      </Grid>
      
      {/* Usage Stats */}
      <Box
        bg="gray.50"
        p={5}
        borderRadius="md"
        mb={6}
      >
        <Heading size="sm" mb={4}>
          <Flex align="center">
            <Icon as={FiBarChart2} mr={2} />
            Music Usage Insights
          </Flex>
        </Heading>
        
        <Grid templateColumns={{ base: '1fr', md: 'repeat(4, 1fr)' }} gap={4}>
          <GridItem>
            <VStack align="start">
              <Text color="gray.500" fontSize="sm">Total Usage</Text>
              <Text fontWeight="bold">{usageStats.totalUsage.toLocaleString()}</Text>
            </VStack>
          </GridItem>
          
          <GridItem>
            <VStack align="start">
              <Text color="gray.500" fontSize="sm">Weekly Plays</Text>
              <Text fontWeight="bold">{usageStats.weeklyPlays.toLocaleString()}</Text>
            </VStack>
          </GridItem>
          
          <GridItem>
            <VStack align="start">
              <Text color="gray.500" fontSize="sm">Monthly Listeners</Text>
              <Text fontWeight="bold">{usageStats.monthlyListeners.toLocaleString()}</Text>
            </VStack>
          </GridItem>
          
          <GridItem>
            <VStack align="start">
              <Text color="gray.500" fontSize="sm">Avg. Royalty per Stream</Text>
              <Text fontWeight="bold">${usageStats.averageRoyalty}</Text>
            </VStack>
          </GridItem>
        </Grid>
      </Box>
      
      {/* Blockchain Information */}
      <Box
        bg="blue.50"
        p={5}
        borderRadius="md"
        borderLeft="4px"
        borderLeftColor="blue.500"
      >
        <Heading size="sm" mb={4}>
          <Flex align="center">
            <Icon as={FiLock} mr={2} />
            Blockchain Security Information
          </Flex>
        </Heading>
        
        <Grid templateColumns={{ base: '1fr', md: 'repeat(3, 1fr)' }} gap={4}>
          <GridItem>
            <VStack align="start" spacing={0}>
              <Text color="gray.500" fontSize="sm">Network</Text>
              <Text fontWeight="bold">Base Mainnet</Text>
            </VStack>
          </GridItem>
          
          <GridItem>
            <VStack align="start" spacing={0}>
              <Text color="gray.500" fontSize="sm">Rights Vault Contract</Text>
              <Tooltip label="View on BaseScan">
                <Text fontWeight="bold" fontSize="sm" fontFamily="mono" cursor="pointer">
                  0x467a7F977b5D0cc22aC3dF56b138228DA77F36B3
                </Text>
              </Tooltip>
            </VStack>
          </GridItem>
          
          <GridItem>
            <VStack align="start" spacing={0}>
              <Text color="gray.500" fontSize="sm">Last Verification</Text>
              <Text fontWeight="bold">{new Date().toLocaleDateString()}</Text>
            </VStack>
          </GridItem>
        </Grid>
      </Box>
    </Box>
  );
} 