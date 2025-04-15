import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { ChatState, ChatMessage, PDFMetadata, ModelConfig } from '../types';

const initialState: ChatState = {
  messages: [],
  documents: [],
  modelConfig: {
    model_type: 'openai',
    temperature: 0.1,
    max_tokens: 512,
    top_p: 0.95,
    repeat_penalty: 1.2,
    n_ctx: 4096,
    gpu_layers: 0,
    embedding_type: 'openai',
  },
  isLoading: false,
  error: null,
};

type StoreState = ChatState & {
  addMessage: (message: ChatMessage) => void;
  setDocuments: (documents: PDFMetadata[]) => void;
  updateModelConfig: (config: Partial<ModelConfig>) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  clearMessages: () => void;
};

export const useStore = create<StoreState>()(
  persist(
    (set) => ({
      ...initialState,
      
      addMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, message],
        })),
        
      setDocuments: (documents) =>
        set(() => ({
          documents,
        })),
        
      updateModelConfig: (config) =>
        set((state) => ({
          modelConfig: { ...state.modelConfig, ...config },
        })),
        
      setLoading: (isLoading) =>
        set(() => ({
          isLoading,
        })),
        
      setError: (error) =>
        set(() => ({
          error,
        })),

      clearMessages: () =>
        set(() => ({
          messages: [],
        })),
    }),
    {
      name: 'chat-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        messages: state.messages,
        modelConfig: {
          ...state.modelConfig,
          model_type: 'openai',
        },
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.updateModelConfig({ model_type: 'openai' });
        }
      },
    }
  )
);
