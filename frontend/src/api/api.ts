import axios from 'axios';
import { ModelConfig, PDFMetadata, ChatMessage } from '../types';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadPDFs = async (files: File[]): Promise<PDFMetadata[]> => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  
  try {
    const response = await api.post('/api/pdf/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    const { document_ids, total_pages } = response.data;
    
    // Convert document IDs to metadata objects
    return document_ids.map((id: string, index: number) => ({
      document_id: id,
      filename: files[index].name,
      page_count: Math.floor(total_pages / files.length) // Approximating page count per file
    }));
  } catch (error) {
    console.error('Error uploading PDFs:', error);
    throw error;
  }
};

export const configureModel = async (config: ModelConfig): Promise<void> => {
  await api.post('/api/model/configure', config);
};

export const uploadLocalModel = async (file: File): Promise<string> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/api/model/upload-local', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data.model_path;
};

export const streamChat = async (
  question: string,
  modelType: string,
  documentIds: string[],
  onChunk: (chunk: string) => void
): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      model_type: modelType,
      session_id: 'default', // TODO: Implement proper session management
      document_ids: documentIds,
    }),
  });

  const reader = response.body?.getReader();
  if (!reader) throw new Error('Failed to get response reader');

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = new TextDecoder().decode(value);
    onChunk(chunk);
  }
};
