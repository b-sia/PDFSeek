import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Text,
  VStack,
  List,
  ListItem,
  CloseButton
} from '@chakra-ui/react';
import { useToast } from '@chakra-ui/toast';
import { useStore } from '../store/useStore';
import { uploadPDFs } from '../api/api';
import { PDFMetadata } from '../types';

export const FileUploader = () => {
  const { documents, setDocuments, setLoading, setError } = useStore();
  const toast = useToast();

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    try {
      setLoading(true);
      const uploadedDocs = await uploadPDFs(acceptedFiles);
      setDocuments([...documents, ...uploadedDocs]);
      toast({
        title: 'Files uploaded successfully',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to upload files');
      toast({
        title: 'Upload failed',
        description: error instanceof Error ? error.message : 'Failed to upload files',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  }, [documents, setDocuments, setLoading, setError, toast]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    multiple: true,
  });

  const removeDocument = (docId: string) => {
    setDocuments(documents.filter(doc => doc.document_id !== docId));
  };

  return (
    <VStack align="stretch" gap={4}>
      <Box
        {...getRootProps()}
        p={6}
        border="2px dashed"
        borderColor={isDragActive ? 'blue.500' : 'gray.200'}
        borderRadius="md"
        cursor="pointer"
        _hover={{ borderColor: 'blue.500' }}
      >
        <input {...getInputProps()} />
        <Text textAlign="center">
          {isDragActive
            ? 'Drop the PDFs here'
            : 'Drag and drop PDFs here, or click to select files'}
        </Text>
      </Box>

      {documents.length > 0 && (
        <Box>
          <Text fontWeight="bold" mb={2}>
            Uploaded Documents
          </Text>
          <List.Root gap={2}>
            {documents.map((doc: PDFMetadata) => (
              <ListItem
                key={doc.document_id}
                display="flex"
                alignItems="center"
                justifyContent="space-between"
                p={2}
                bg="gray.50"
                borderRadius="md"
              >
                <Text>{doc.filename}</Text>
                <CloseButton
                  aria-label="Remove document"
                  size="sm"
                  onClick={() => removeDocument(doc.document_id)}
                  colorScheme="red"
                />
              </ListItem>
            ))}
          </List.Root>
        </Box>
      )}
    </VStack>
  );
};
