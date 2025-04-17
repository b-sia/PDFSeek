import { useState } from 'react';
import {
  VStack,
  Select,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Button,
  Collapse,
  Text,
  Box,
  HStack,
  Progress,
} from '@chakra-ui/react';
import { FormControl, FormLabel } from '@chakra-ui/form-control';
import { useToast } from '@chakra-ui/toast';
import { useStore } from '../store/useStore';
import { configureModel, uploadLocalModel } from '../api/api';
import { ModelConfig } from '../types';

export const ModelConfigPanel = () => {
  const { modelConfig, updateModelConfig, setLoading, setError } = useStore();
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [_, setLocalModelFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const toast = useToast();

  const handleModelTypeChange = async (value: string) => {
    const modelType = value as 'openai' | 'local';
    
    // Update local state first
    updateModelConfig({ model_type: modelType });
    
    // Immediately save the configuration to the backend
    try {
      setLoading(true);
      await configureModel({
        ...modelConfig,
        model_type: modelType
        // Let the backend set the embedding_type automatically
      });
      toast({
        title: 'Model type updated',
        description: `Changed to ${modelType} model`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to update model type');
      toast({
        title: 'Update failed',
        description: error instanceof Error ? error.message : 'Failed to update model type',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleLocalModelUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLocalModelFile(file);
    try {
      setIsUploading(true);
      setUploadProgress(0);
      setLoading(true);
      const modelPath = await uploadLocalModel(file, (progress) => {
        setUploadProgress(progress);
      });
      updateModelConfig({ model_path: modelPath });
      toast({
        title: 'Model uploaded successfully',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to upload model');
      toast({
        title: 'Upload failed',
        description: error instanceof Error ? error.message : 'Failed to upload model',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleSaveConfig = async () => {
    try {
      setLoading(true);
      await configureModel(modelConfig);
      toast({
        title: 'Configuration saved',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to save configuration');
      toast({
        title: 'Save failed',
        description: error instanceof Error ? error.message : 'Failed to save configuration',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <VStack spacing={4} align="stretch">
      <FormControl>
        <FormLabel htmlFor="model-type">Model Type</FormLabel>
        <Select
          id="model-type"
          value={modelConfig.model_type}
          onChange={(e: any) => handleModelTypeChange(e.target.value)}
        >
          <option value="openai">OpenAI GPT-3.5</option>
          <option value="local">Local LLM</option>
        </Select>
        <Text fontSize="xs" color="gray.500" mt={1}>
          {modelConfig.model_type === 'openai' 
            ? 'Uses OpenAI embeddings for document search' 
            : 'Uses HuggingFace embeddings for document search'}
        </Text>
      </FormControl>

      {modelConfig.model_type === 'local' && (
        <FormControl>
          <FormLabel htmlFor="model-upload">Upload Local Model</FormLabel>
          <input
            id="model-upload"
            type="file"
            accept=".gguf,.safetensors,.bin,.pt"
            onChange={handleLocalModelUpload}
            disabled={isUploading}
            aria-label="Upload Local Model"
            data-testid="model-upload-input"
          />
          {isUploading && (
            <Box mt={2}>
              <HStack justify="space-between" mb={1}>
                <Text fontSize="sm">Upload Progress</Text>
                <Text fontSize="sm">{Math.round(uploadProgress)}%</Text>
              </HStack>
              <Progress value={uploadProgress} size="sm" colorScheme="blue" />
            </Box>
          )}
          {modelConfig.model_path && !isUploading && (
            <Text fontSize="sm" color="green.500" mt={2}>
              Using model: {modelConfig.model_path}
            </Text>
          )}
        </FormControl>
      )}

      <Button onClick={() => setShowAdvanced(!showAdvanced)}>
        {showAdvanced ? 'Hide Advanced Settings' : 'Show Advanced Settings'}
      </Button>

      <Collapse in={showAdvanced}>
        <VStack spacing={4} align="stretch">
          <FormControl>
            <FormLabel htmlFor="temperature">Temperature</FormLabel>
            <NumberInput
              id="temperature"
              value={modelConfig.temperature}
              onChange={(_: any, value: any) => updateModelConfig({ temperature: value })}
              min={0}
              max={1}
              step={0.01}
            >
              <NumberInputField />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>

          <FormControl>
            <FormLabel htmlFor="max-tokens">Max Tokens</FormLabel>
            <NumberInput
              id="max-tokens"
              value={modelConfig.max_tokens}
              onChange={(_: any, value: any) => updateModelConfig({ max_tokens: value })}
              min={100}
              max={4096}
              step={100}
            >
              <NumberInputField />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>

          <FormControl>
            <FormLabel htmlFor="top-p">Top P</FormLabel>
            <NumberInput
              id="top-p"
              value={modelConfig.top_p}
              onChange={(_: any, value: any) => updateModelConfig({ top_p: value })}
              min={0}
              max={1}
              step={0.01}
            >
              <NumberInputField />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>

          <FormControl>
            <FormLabel htmlFor="repeat-penalty">Repeat Penalty</FormLabel>
            <NumberInput
              id="repeat-penalty"
              value={modelConfig.repeat_penalty}
              onChange={(_: any, value: any) => updateModelConfig({ repeat_penalty: value })}
              min={0}
              max={2}
              step={0.1}
            >
              <NumberInputField />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>

          <FormControl>
            <FormLabel htmlFor="context-length">Context Length</FormLabel>
            <NumberInput
              id="context-length"
              value={modelConfig.n_ctx}
              onChange={(_: any, value: any) => updateModelConfig({ n_ctx: value })}
              min={1}
              max={4096}
              step={1}
            >
              <NumberInputField />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>

          <FormControl>
            <FormLabel htmlFor="gpu-layers">GPU Layers</FormLabel>
            <NumberInput
              id="gpu-layers"
              value={modelConfig.gpu_layers}
              onChange={(_: any, value: any) => updateModelConfig({ gpu_layers: value })}
              min={-1}
              max={100}
              step={1}
            >
              <NumberInputField />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>
        </VStack>
      </Collapse>

      <Button colorScheme="blue" onClick={handleSaveConfig}>
        Save Configuration
      </Button>
    </VStack>
  );
};
