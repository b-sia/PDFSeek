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
  Collapsible,
  Text,
} from '@chakra-ui/react';
import { FormControl, FormLabel } from '@chakra-ui/form-control';
import { useToast } from '@chakra-ui/toast';
import { useStore } from '../store/useStore';
import { configureModel, uploadLocalModel } from '../api/api';
import { ModelConfig } from '../types';

export const ModelConfigPanel = () => {
  const { modelConfig, updateModelConfig, setLoading, setError } = useStore();
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [setLocalModelFile] = useState<File | null>(null);
  const toast = useToast();

  const handleModelTypeChange = (value: string) => {
    updateModelConfig({ model_type: value as 'openai' | 'local' });
  };

  const handleLocalModelUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLocalModelFile(file);
    try {
      setLoading(true);
      const modelPath = await uploadLocalModel(file);
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
    <VStack gap={4} align="stretch">
      <FormControl>
        <FormLabel>Model Type</FormLabel>
        <Select
          value={modelConfig.model_type}
          onChange={(e: any) => handleModelTypeChange(e.target.value)}
        >
          <option value="openai">OpenAI GPT-3.5</option>
          <option value="local">Local LLM</option>
        </Select>
      </FormControl>

      {modelConfig.model_type === 'local' && (
        <FormControl>
          <FormLabel>Upload Local Model</FormLabel>
          <input
            type="file"
            accept=".gguf,.safetensors,.bin,.pt"
            onChange={handleLocalModelUpload}
          />
          {modelConfig.model_path && (
            <Text fontSize="sm" color="green.500" mt={2}>
              Using model: {modelConfig.model_path}
            </Text>
          )}
        </FormControl>
      )}

      <Button onClick={() => setShowAdvanced(!showAdvanced)}>
        {showAdvanced ? 'Hide Advanced Settings' : 'Show Advanced Settings'}
      </Button>

      <Collapsible.Root open={showAdvanced}>
        <VStack gap={4} align="stretch">
          <FormControl>
            <FormLabel>Temperature</FormLabel>
            <NumberInput
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
            <FormLabel>Max Tokens</FormLabel>
            <NumberInput
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
            <FormLabel>Top P</FormLabel>
            <NumberInput
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
            <FormLabel>Repeat Penalty</FormLabel>
            <NumberInput
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
            <FormLabel>Context Length</FormLabel>
            <NumberInput
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
            <FormLabel>GPU Layers</FormLabel>
            <NumberInput
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
      </Collapsible.Root>

      <Button colorScheme="blue" onClick={handleSaveConfig}>
        Save Configuration
      </Button>
    </VStack>
  );
};
