import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatInterface } from '../ChatInterface';
import { useStore } from '../../store/useStore';
import { streamChat } from '../../api/api';
import { ChatMessage } from '../../types';

// Mock the store
vi.mock('../../store/useStore', () => ({
  useStore: vi.fn(),
}));

// Mock the API
vi.mock('../../api/api', () => ({
  streamChat: vi.fn(),
}));

// Mock the toast
vi.mock('@chakra-ui/toast', () => ({
  useToast: () => vi.fn(),
}));

describe('ChatInterface', () => {
  const mockAddMessage = vi.fn();
  const mockSetLoading = vi.fn();
  const mockSetError = vi.fn();
  const mockClearMessages = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useStore as any).mockReturnValue({
      messages: [],
      documents: [{ document_id: '1', filename: 'test.pdf' }],
      modelConfig: { model_type: 'openai' },
      isLoading: false,
      addMessage: mockAddMessage,
      setLoading: mockSetLoading,
      setError: mockSetError,
      clearMessages: mockClearMessages,
    });
  });

  it('renders chat interface with empty state', () => {
    render(<ChatInterface />);
    expect(screen.getByPlaceholderText('Ask a question about your documents...')).toBeInTheDocument();
    expect(screen.getByText('Send')).toBeInTheDocument();
  });

  it('clears messages on mount', () => {
    render(<ChatInterface />);
    expect(mockClearMessages).toHaveBeenCalled();
  });

  it('handles user message submission', async () => {
    const mockResponse = 'This is a test response';
    (streamChat as any).mockImplementation((
      message: string,
      modelType: string,
      documentIds: string[],
      callback: (chunk: string) => void
    ) => {
      callback(mockResponse);
      return Promise.resolve();
    });

    render(<ChatInterface />);
    const input = screen.getByPlaceholderText('Ask a question about your documents...');
    const sendButton = screen.getByText('Send');

    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(mockAddMessage).toHaveBeenCalledWith({
        role: 'user',
        content: 'Test question',
        timestamp: expect.any(Date),
      });
      expect(mockSetLoading).toHaveBeenCalledWith(true);
      expect(streamChat).toHaveBeenCalledWith(
        'Test question',
        'openai',
        ['1'],
        expect.any(Function)
      );
      expect(mockAddMessage).toHaveBeenCalledWith({
        role: 'assistant',
        content: mockResponse,
        timestamp: expect.any(Date),
      });
      expect(mockSetLoading).toHaveBeenCalledWith(false);
    });
  });

  it('handles streaming response', async () => {
    const chunks = ['Hello', ' world', '!'];
    (streamChat as any).mockImplementation((
      message: string,
      modelType: string,
      documentIds: string[],
      callback: (chunk: string) => void
    ) => {
      chunks.forEach(chunk => callback(chunk));
      return Promise.resolve();
    });

    render(<ChatInterface />);
    const input = screen.getByPlaceholderText('Ask a question about your documents...');
    const sendButton = screen.getByText('Send');

    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(mockAddMessage).toHaveBeenCalledWith({
        role: 'assistant',
        content: 'Hello world!',
        timestamp: expect.any(Date),
      });
    });
  });

  it('disables input when no documents are loaded', () => {
    (useStore as any).mockReturnValue({
      messages: [],
      documents: [],
      modelConfig: { model_type: 'openai' },
      isLoading: false,
      addMessage: mockAddMessage,
      setLoading: mockSetLoading,
      setError: mockSetError,
      clearMessages: mockClearMessages,
    });

    render(<ChatInterface />);
    const input = screen.getByPlaceholderText('Ask a question about your documents...');
    const sendButton = screen.getByText('Send');

    expect(input).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });

  it('disables input while loading', () => {
    (useStore as any).mockReturnValue({
      messages: [],
      documents: [{ document_id: '1', filename: 'test.pdf' }],
      modelConfig: { model_type: 'openai' },
      isLoading: true,
      addMessage: mockAddMessage,
      setLoading: mockSetLoading,
      setError: mockSetError,
      clearMessages: mockClearMessages,
    });

    render(<ChatInterface />);
    const input = screen.getByPlaceholderText('Ask a question about your documents...');
    const sendButton = screen.getByRole('button', { name: /Loading.*Send/i });

    expect(input).toBeDisabled();
    expect(sendButton).toHaveAttribute('disabled');
  });

  it('handles chat error', async () => {
    const mockError = new Error('Chat failed');
    (streamChat as any).mockRejectedValueOnce(mockError);

    render(<ChatInterface />);
    const input = screen.getByPlaceholderText('Ask a question about your documents...');
    const sendButton = screen.getByText('Send');

    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(mockSetError).toHaveBeenCalledWith('Chat failed');
      expect(mockSetLoading).toHaveBeenCalledWith(true);
      expect(mockSetLoading).toHaveBeenCalledWith(false);
    });
  });

  it('displays messages in the chat', () => {
    const mockMessages: ChatMessage[] = [
      { role: 'user', content: 'Hello', timestamp: new Date() },
      { role: 'assistant', content: 'Hi there!', timestamp: new Date() },
    ];

    (useStore as any).mockReturnValue({
      messages: mockMessages,
      documents: [{ document_id: '1', filename: 'test.pdf' }],
      modelConfig: { model_type: 'openai' },
      isLoading: false,
      addMessage: mockAddMessage,
      setLoading: mockSetLoading,
      setError: mockSetError,
      clearMessages: mockClearMessages,
    });

    render(<ChatInterface />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there!')).toBeInTheDocument();
  });
}); 