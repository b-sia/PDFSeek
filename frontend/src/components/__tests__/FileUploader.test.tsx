import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChakraProvider } from '@chakra-ui/react';
import { FileUploader } from '../FileUploader';
import { useStore } from '../../store/useStore';
import { uploadPDFs } from '../../api/api';

// Mock the store
vi.mock('../../store/useStore', () => ({
  useStore: vi.fn(),
}));

// Mock the API
vi.mock('../../api/api', () => ({
  uploadPDFs: vi.fn(),
}));

// Mock the toast
vi.mock('@chakra-ui/toast', () => ({
  useToast: () => vi.fn(),
}));

const renderWithChakra = (ui: React.ReactElement) => {
  return render(
    <ChakraProvider>{ui}</ChakraProvider>
  );
};

describe('FileUploader', () => {
  const mockSetDocuments = vi.fn();
  const mockSetLoading = vi.fn();
  const mockSetError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useStore as any).mockReturnValue({
      documents: [],
      setDocuments: mockSetDocuments,
      setLoading: mockSetLoading,
      setError: mockSetError,
    });
  });

  it('renders the upload area with correct initial text', () => {
    renderWithChakra(<FileUploader />);
    expect(screen.getByText(/Drag and drop PDFs here, or click to select files/i)).toBeInTheDocument();
  });

  it('shows drag active state when files are dragged over', async () => {
    renderWithChakra(<FileUploader />);
    const dropzone = screen.getByText(/Drag and drop PDFs here/i).parentElement!;
    
    // Create a dragenter event with files
    const dragEnterEvent = new Event('dragenter', { bubbles: true });
    Object.defineProperty(dragEnterEvent, 'dataTransfer', {
      value: {
        types: ['Files'],
        files: [new File(['test'], 'test.pdf', { type: 'application/pdf' })],
      },
    });
    
    await act(async () => {
      fireEvent(dropzone, dragEnterEvent);
    });

    // Check for the drag active text instead of style
    expect(screen.getByText('Drop the PDFs here')).toBeInTheDocument();
  });

  it('handles file upload successfully', async () => {
    const mockFiles = [new File(['test'], 'test.pdf', { type: 'application/pdf' })];
    const mockUploadedDocs = [{ document_id: '1', filename: 'test.pdf' }];
    
    (uploadPDFs as any).mockResolvedValueOnce(mockUploadedDocs);

    renderWithChakra(<FileUploader />);
    const dropzone = screen.getByText(/Drag and drop PDFs here/i).parentElement!;
    const input = dropzone.querySelector('input')!;
    
    // Simulate file selection through input
    fireEvent.change(input, { target: { files: mockFiles } });

    await waitFor(() => {
      expect(mockSetLoading).toHaveBeenCalledWith(true);
      expect(uploadPDFs).toHaveBeenCalledWith(mockFiles, expect.any(Function));
      expect(mockSetDocuments).toHaveBeenCalledWith([...mockUploadedDocs]);
      expect(mockSetLoading).toHaveBeenCalledWith(false);
    });
  });

  it('handles file upload error', async () => {
    const mockFiles = [new File(['test'], 'test.pdf', { type: 'application/pdf' })];
    const mockError = new Error('Upload failed');
    
    (uploadPDFs as any).mockRejectedValueOnce(mockError);

    renderWithChakra(<FileUploader />);
    const dropzone = screen.getByText(/Drag and drop PDFs here/i).parentElement!;
    const input = dropzone.querySelector('input')!;
    
    // Simulate file selection through input
    fireEvent.change(input, { target: { files: mockFiles } });

    await waitFor(() => {
      expect(mockSetError).toHaveBeenCalledWith('Upload failed');
      expect(mockSetLoading).toHaveBeenCalledWith(true);
      expect(mockSetLoading).toHaveBeenCalledWith(false);
    });
  });

  it('displays uploaded documents and allows removal', () => {
    const mockDocuments = [
      { document_id: '1', filename: 'test1.pdf' },
      { document_id: '2', filename: 'test2.pdf' },
    ];

    (useStore as any).mockReturnValue({
      documents: mockDocuments,
      setDocuments: mockSetDocuments,
      setLoading: mockSetLoading,
      setError: mockSetError,
    });

    renderWithChakra(<FileUploader />);
    
    expect(screen.getByText('test1.pdf')).toBeInTheDocument();
    expect(screen.getByText('test2.pdf')).toBeInTheDocument();

    const removeButtons = screen.getAllByLabelText('Remove document');
    fireEvent.click(removeButtons[0]);

    expect(mockSetDocuments).toHaveBeenCalledWith([mockDocuments[1]]);
  });
}); 