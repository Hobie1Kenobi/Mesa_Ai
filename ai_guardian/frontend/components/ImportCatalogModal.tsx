import { useState, useRef, useCallback } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  Box,
  Text,
  FormControl,
  FormLabel,
  Input,
  VStack,
  Progress,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Alert,
  AlertIcon,
  Flex,
  Icon,
  useToast
} from '@chakra-ui/react';
import { FiUploadCloud, FiFile, FiCheck, FiX } from 'react-icons/fi';

interface ImportCatalogModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportComplete: (data: any[]) => void;
}

export default function ImportCatalogModal({ 
  isOpen, 
  onClose, 
  onImportComplete 
}: ImportCatalogModalProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [previewData, setPreviewData] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const toast = useToast();

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const processCSV = (text: string) => {
    try {
      // Basic CSV parsing
      const lines = text.split('\n').filter(line => line.trim() !== '');
      const headers = lines[0].split(',');
      
      const result = [];
      
      // Process only first 10 lines for preview
      const previewLines = lines.slice(1, Math.min(11, lines.length));
      
      for (const line of previewLines) {
        if (line.trim() === '') continue;
        
        const values = line.split(',');
        const entry: any = {};
        
        // Map CSV fields to our data model
        entry.title = values[0] || '';
        entry.artist = values[1] || '';
        entry.isrc = values[10] || '';
        entry.iswc = values[11] || '';
        entry.year = values[13] || '';
        entry.status = 'pending'; // Default status for imported tracks
        entry.rightsId = null;
        entry.publisher = values[9] || '';
        
        result.push(entry);
      }
      
      setPreviewData(result);
      return {
        headers,
        totalRows: lines.length - 1,
        preview: result
      };
    } catch (err) {
      console.error("Error processing CSV:", err);
      setError("Failed to process CSV file. Please check the format.");
      return null;
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    setError(null);
    
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
        setError("Please upload a CSV file");
        return;
      }
      
      setFile(file);
      
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          const text = event.target.result as string;
          processCSV(text);
        }
      };
      reader.readAsText(file);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
        setError("Please upload a CSV file");
        return;
      }
      
      setFile(file);
      
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          const text = event.target.result as string;
          processCSV(text);
        }
      };
      reader.readAsText(file);
    }
  };

  const handleImport = () => {
    if (!file) return;
    
    setIsLoading(true);
    setProgress(0);
    
    // Simulate processing with progress
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          
          // Finish import
          setTimeout(() => {
            setIsLoading(false);
            
            // Process the full CSV here
            const reader = new FileReader();
            reader.onload = (event) => {
              if (event.target?.result) {
                const text = event.target.result as string;
                const result = processCSV(text);
                
                if (result) {
                  // In a real app, we would process all rows
                  // For demo purposes, we'll just convert preview data to the expected format
                  const importedData = previewData.map((item, index) => ({
                    id: Date.now() + index,
                    title: item.title,
                    artist: item.artist,
                    isrc: item.isrc,
                    iswc: item.iswc,
                    year: item.year,
                    status: 'registered', // Set as registered after "processing"
                    rightsId: `0x${Math.random().toString(16).substring(2, 10)}...${Math.random().toString(16).substring(2, 6)}`,
                    txHash: `0x${Math.random().toString(16).substring(2, 10)}...${Math.random().toString(16).substring(2, 6)}`,
                    timestamp: new Date().toISOString(),
                    publisher: item.publisher
                  }));
                  
                  toast({
                    title: 'Import successful',
                    description: `Imported ${importedData.length} tracks from "${file.name}"`,
                    status: 'success',
                    duration: 5000,
                    isClosable: true,
                  });
                  
                  onImportComplete(importedData);
                  onClose();
                }
              }
            };
            reader.readAsText(file);
          }, 500);
          
          return 100;
        }
        return prev + 5;
      });
    }, 100);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Import Music Catalog</ModalHeader>
        <ModalCloseButton />
        
        <ModalBody>
          <VStack spacing={4}>
            {error && (
              <Alert status="error">
                <AlertIcon />
                {error}
              </Alert>
            )}
            
            <input
              type="file"
              accept=".csv"
              ref={fileInputRef}
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
            
            {!file ? (
              <Box
                border="2px dashed"
                borderColor={isDragging ? "blue.400" : "gray.200"}
                borderRadius="md"
                p={10}
                textAlign="center"
                bg={isDragging ? "blue.50" : "gray.50"}
                width="100%"
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                cursor="pointer"
                onClick={() => fileInputRef.current?.click()}
                transition="all 0.2s"
              >
                <Icon as={FiUploadCloud} boxSize={10} color="gray.400" mb={2} />
                <Text fontWeight="bold" mb={1}>
                  Drag and drop your CSV file here
                </Text>
                <Text fontSize="sm" color="gray.500">
                  or click to browse
                </Text>
              </Box>
            ) : (
              <>
                <Flex 
                  align="center" 
                  justify="space-between" 
                  width="100%" 
                  p={3} 
                  bg="gray.50" 
                  borderRadius="md"
                >
                  <Flex align="center">
                    <Icon as={FiFile} mr={2} color="blue.500" />
                    <Text fontWeight="medium">{file.name}</Text>
                  </Flex>
                  
                  <Button 
                    size="sm" 
                    colorScheme="red" 
                    variant="ghost" 
                    onClick={() => {
                      setFile(null);
                      setPreviewData([]);
                    }}
                  >
                    Remove
                  </Button>
                </Flex>
                
                {isLoading && (
                  <Box width="100%" mt={3}>
                    <Text mb={1}>Processing file... {progress}%</Text>
                    <Progress value={progress} size="sm" colorScheme="blue" />
                  </Box>
                )}
                
                {previewData.length > 0 && (
                  <Box width="100%" overflowX="auto">
                    <Text fontWeight="bold" mb={2}>Preview:</Text>
                    <Table size="sm" variant="simple">
                      <Thead>
                        <Tr>
                          <Th>Title</Th>
                          <Th>Artist</Th>
                          <Th>ISRC</Th>
                          <Th>Year</Th>
                          <Th>Publisher</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {previewData.map((item, index) => (
                          <Tr key={index}>
                            <Td>{item.title}</Td>
                            <Td>{item.artist}</Td>
                            <Td>{item.isrc}</Td>
                            <Td>{item.year}</Td>
                            <Td>{item.publisher}</Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                    <Text fontSize="sm" color="gray.500" mt={2}>
                      Showing {previewData.length} of {file ? 'many' : '0'} entries
                    </Text>
                  </Box>
                )}
              </>
            )}
          </VStack>
        </ModalBody>

        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            Cancel
          </Button>
          <Button 
            colorScheme="blue" 
            leftIcon={<FiCheck />}
            onClick={handleImport}
            isLoading={isLoading}
            loadingText="Importing..."
            isDisabled={!file || isLoading}
          >
            Import Catalog
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
} 