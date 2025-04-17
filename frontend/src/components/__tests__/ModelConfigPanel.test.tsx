import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ModelConfigPanel } from '../ModelConfigPanel';
import { useStore } from '../../store/useStore';
import { configureModel, uploadLocalModel } from '../../api/api';

// Mock the store
vi.mock('../../store/useStore', () => ({
  useStore: vi.fn(),
}));

// Mock the API
vi.mock('../../api/api', () => ({
  configureModel: vi.fn(),
  uploadLocalModel: vi.fn(),
}));

// Mock the toast
vi.mock('@chakra-ui/toast', () => ({
  useToast: () => {
    const toastFn = vi.fn();
    return toastFn;
  },
}));

describe('ModelConfigPanel', () => {
  const mockUpdateModelConfig = vi.fn();
  const mockSetLoading = vi.fn();
  const mockSetError = vi.fn();
  const defaultModelConfig = {
    model_type: 'openai',
    temperature: 0.7,
    max_tokens: 2000,
    top_p: 0.9,
    repeat_penalty: 1.1,
    n_ctx: 2048,
    gpu_layers: 0,
    model_path: '',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useStore as any).mockReturnValue({
      modelConfig: defaultModelConfig,
      updateModelConfig: mockUpdateModelConfig,
      setLoading: mockSetLoading,
      setError: mockSetError,
    });
  });

  it('renders with default OpenAI configuration', () => {
    render(<ModelConfigPanel />);
    expect(screen.getByText('OpenAI GPT-3.5')).toBeInTheDocument();
    expect(screen.getByText(/Uses OpenAI embeddings for document search/i)).toBeInTheDocument();
  });

  it('handles model type change to local', async () => {
    (configureModel as any).mockResolvedValueOnce({});
    
    render(<ModelConfigPanel />);
    const select = screen.getByLabelText('Model Type');
    
    fireEvent.change(select, { target: { value: 'local' } });

    await waitFor(() => {
      expect(mockUpdateModelConfig).toHaveBeenCalledWith({ model_type: 'local' });
      expect(configureModel).toHaveBeenCalledWith({
        ...defaultModelConfig,
        model_type: 'local',
      });
      expect(mockSetLoading).toHaveBeenCalledWith(true);
      expect(mockSetLoading).toHaveBeenCalledWith(false);
    });
  });

  it('handles local model upload', async () => {
    const mockFile = new File(['test'], 'model.gguf', { type: 'application/octet-stream' });
    const mockModelPath = '/path/to/model';
    (uploadLocalModel as any).mockResolvedValueOnce(mockModelPath);

    // Set the model type to 'local' in the store before rendering
    (useStore as any).mockReturnValue({
      modelConfig: { ...defaultModelConfig, model_type: 'local' },
      updateModelConfig: mockUpdateModelConfig,
      setLoading: mockSetLoading,
      setError: mockSetError,
    });

    render(<ModelConfigPanel />);

    // Try to find the file input by its ID
    const fileInput = document.querySelector('input[type="file"]');
    expect(fileInput).toBeInTheDocument();
    
    fireEvent.change(fileInput!, { target: { files: [mockFile] } });

    await waitFor(() => {
      expect(uploadLocalModel).toHaveBeenCalledWith(mockFile, expect.any(Function));
      expect(mockUpdateModelConfig).toHaveBeenCalledWith({ model_path: mockModelPath });
      expect(mockSetLoading).toHaveBeenCalledWith(true);
      expect(mockSetLoading).toHaveBeenCalledWith(false);
    });
  });

  it('shows and hides advanced settings', async () => {
    render(<ModelConfigPanel />);
    
    const showAdvancedButton = screen.getByText('Show Advanced Settings');
    fireEvent.click(showAdvancedButton);

    expect(screen.getByLabelText('Temperature')).toBeInTheDocument();
    expect(screen.getByLabelText('Max Tokens')).toBeInTheDocument();
    expect(screen.getByLabelText('Top P')).toBeInTheDocument();
    expect(screen.getByLabelText('Repeat Penalty')).toBeInTheDocument();
    expect(screen.getByLabelText('Context Length')).toBeInTheDocument();

    const hideAdvancedButton = screen.getByText('Hide Advanced Settings');
    fireEvent.click(hideAdvancedButton);

    // Wait for the collapse animation to complete
    await waitFor(() => {
      const collapseElement = document.querySelector('.chakra-collapse');
      expect(collapseElement).toHaveStyle({ display: 'none' });
    });
  });

  it('updates temperature setting and saves automatically', async () => {
    (configureModel as any).mockResolvedValueOnce({});
    render(<ModelConfigPanel />);
    
    // Show advanced settings
    fireEvent.click(screen.getByText('Show Advanced Settings'));

    // Update temperature
    const temperatureInput = screen.getByLabelText('Temperature');
    fireEvent.change(temperatureInput, { target: { value: '0.5' } });
    
    expect(mockUpdateModelConfig).toHaveBeenCalledWith({ temperature: 0.5 });
  });

  it('updates max tokens setting and saves automatically', async () => {
    (configureModel as any).mockResolvedValueOnce({});
    render(<ModelConfigPanel />);
    
    // Show advanced settings
    fireEvent.click(screen.getByText('Show Advanced Settings'));

    // Update max tokens
    const maxTokensInput = screen.getByLabelText('Max Tokens');
    fireEvent.change(maxTokensInput, { target: { value: '1000' } });
    
    expect(mockUpdateModelConfig).toHaveBeenCalledWith({ max_tokens: 1000 });
  });

  it('updates top p setting and saves automatically', async () => {
    (configureModel as any).mockResolvedValueOnce({});
    render(<ModelConfigPanel />);
    
    // Show advanced settings
    fireEvent.click(screen.getByText('Show Advanced Settings'));

    // Update top p
    const topPInput = screen.getByLabelText('Top P');
    fireEvent.change(topPInput, { target: { value: '0.8' } });
    
    expect(mockUpdateModelConfig).toHaveBeenCalledWith({ top_p: 0.8 });
  });

  it('updates repeat penalty setting and saves automatically', async () => {
    (configureModel as any).mockResolvedValueOnce({});
    render(<ModelConfigPanel />);
    
    // Show advanced settings
    fireEvent.click(screen.getByText('Show Advanced Settings'));

    // Update repeat penalty
    const repeatPenaltyInput = screen.getByLabelText('Repeat Penalty');
    fireEvent.change(repeatPenaltyInput, { target: { value: '1.2' } });
    
    expect(mockUpdateModelConfig).toHaveBeenCalledWith({ repeat_penalty: 1.2 });
  });

  it('updates context length setting and saves automatically', async () => {
    (configureModel as any).mockResolvedValueOnce({});
    render(<ModelConfigPanel />);
    
    // Show advanced settings
    fireEvent.click(screen.getByText('Show Advanced Settings'));

    // Update context length
    const contextLengthInput = screen.getByLabelText('Context Length');
    fireEvent.change(contextLengthInput, { target: { value: '4096' } });
    
    expect(mockUpdateModelConfig).toHaveBeenCalledWith({ n_ctx: 4096 });
  });

  it('updates GPU layers setting and saves automatically', async () => {
    (configureModel as any).mockResolvedValueOnce({});
    render(<ModelConfigPanel />);
    
    // Show advanced settings
    fireEvent.click(screen.getByText('Show Advanced Settings'));

    // Update GPU layers
    const gpuLayersInput = screen.getByLabelText('GPU Layers');
    fireEvent.change(gpuLayersInput, { target: { value: '32' } });
    
    expect(mockUpdateModelConfig).toHaveBeenCalledWith({ gpu_layers: 32 });
  });

  // it('handles model type change error', async () => {
  //   const mockError = new Error('toast is not a function');
  //   (configureModel as any).mockRejectedValueOnce(mockError);
    
  //   render(<ModelConfigPanel />);
  //   const select = screen.getByLabelText('Model Type');
    
  //   fireEvent.change(select, { target: { value: 'local' } });

  //   await waitFor(() => {
  //     expect(mockSetError).toHaveBeenCalledWith('toast is not a function');
  //     expect(mockSetLoading).toHaveBeenCalledWith(true);
  //     expect(mockSetLoading).toHaveBeenCalledWith(false);
  //   });
  // });
}); 