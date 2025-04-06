export interface ModelConfig {
  model_type: 'openai' | 'local';
  temperature: number;
  max_tokens: number;
  top_p: number;
  repeat_penalty: number;
  n_ctx: number;
  gpu_layers: number;
  model_path?: string;
  embedding_type?: 'openai' | 'huggingface';
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: string[];
}

export interface PDFMetadata {
  filename: string;
  page_count: number;
  document_id: string;
}

export interface ChatState {
  messages: ChatMessage[];
  documents: PDFMetadata[];
  modelConfig: ModelConfig;
  isLoading: boolean;
  error: string | null;
}
