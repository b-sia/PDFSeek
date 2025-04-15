import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Text,
  VStack,
  List,
  ListItem,
  CloseButton,
  Progress,
  HStack,
} from '@chakra-ui/react';
import { useToast } from '@chakra-ui/toast';
import { useStore } from '../store/useStore';
import { uploadPDFs } from '../api/api';
import { PDFMetadata } from '../types';

export const FileUploader = () => {
  const { documents, setDocuments, setLoading, setError } = useStore();
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const toast = useToast();

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    try {
      setIsUploading(true);
      setUploadProgress(0);
      setLoading(true);
      const uploadedDocs = await uploadPDFs(acceptedFiles, (progress) => {
        setUploadProgress(progress);
      });
      setDocuments([...documents, ...uploadedDocs]);
      toast({
        title: 'Files uploaded successfully',
        description: `Uploaded ${uploadedDocs.length} file(s)`,
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
      setIsUploading(false);
      setUploadProgress(0);
    }
  }, [documents, setDocuments, setLoading, setError, toast]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    multiple: true,
    disabled: isUploading,
  });

  const removeDocument = (docId: string) => {
    setDocuments(documents.filter(doc => doc.document_id !== docId));
  };

  return (
    <VStack align="stretch" spacing={4}>
      <Box
        {...getRootProps()}
        p={6}
        border="2px dashed"
        borderColor={isDragActive ? 'blue.500' : 'gray.200'}
        borderRadius="md"
        cursor={isUploading ? 'not-allowed' : 'pointer'}
        _hover={{ borderColor: isUploading ? 'gray.200' : 'blue.500' }}
        opacity={isUploading ? 0.7 : 1}
      >
        <input {...getInputProps()} />
        <Text textAlign="center">
          {isUploading
            ? 'Uploading...'
            : isDragActive
            ? 'Drop the PDFs here'
            : 'Drag and drop PDFs here, or click to select files'}
        </Text>
      </Box>

      {isUploading && (
        <Box>
          <HStack justify="space-between" mb={1}>
            <Text fontSize="sm">Upload Progress</Text>
            <Text fontSize="sm">{Math.round(uploadProgress)}%</Text>
          </HStack>
          <Progress value={uploadProgress} size="sm" colorScheme="blue" />
        </Box>
      )}

      {documents.length > 0 && (
        <Box>
          <Text fontWeight="bold" mb={2}>
            Uploaded Documents
          </Text>
          <List spacing={2}>
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
          </List>
        </Box>
      )}
    </VStack>
  );
};
