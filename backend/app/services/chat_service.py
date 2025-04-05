import os
from typing import AsyncGenerator, Dict, List
from langchain_openai import ChatOpenAI
from langchain_community.llms import LlamaCpp
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from app.models.chat import ChatRequest, ChatResponse
from app.core.config import settings
from app.services.vector_store import get_vector_store

class ChatService:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.vector_store = get_vector_store()

    async def _get_llm(self, model_type: str, model_path: str = None) -> ChatOpenAI | LlamaCpp:
        if model_type == "openai":
            return ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=settings.DEFAULT_TEMPERATURE,
                max_tokens=settings.DEFAULT_MAX_TOKENS,
                streaming=True
            )
        elif model_type == "local":
            if not model_path:
                raise ValueError("Model path is required for local models")
            return LlamaCpp(
                model_path=model_path,
                temperature=settings.DEFAULT_TEMPERATURE,
                max_tokens=settings.DEFAULT_MAX_TOKENS,
                top_p=settings.DEFAULT_TOP_P,
                repeat_penalty=settings.DEFAULT_REPEAT_PENALTY,
                n_ctx=settings.DEFAULT_N_CTX,
                n_gpu_layers=settings.DEFAULT_GPU_LAYERS,
                streaming=True
            )
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

    async def _get_chain(self, llm, document_ids: List[str]):
        # Get relevant documents from vector store
        docs = []
        for doc_id in document_ids:
            doc = self.vector_store.get_document(doc_id)
            if doc:
                docs.extend(self.text_splitter.split_text(doc))

        # Create vector store from documents
        doc_vector_store = FAISS.from_texts(
            docs,
            self.embeddings
        )

        # Create chain
        return ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=doc_vector_store.as_retriever(),
            memory=self.memory,
            return_source_documents=True
        )

    async def process_chat_request(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        try:
            # Get LLM based on model type
            llm = await self._get_llm(request.model_type)
            
            # Get chain with relevant documents
            chain = await self._get_chain(llm, request.document_ids or [])

            # Process the chat request
            response = await chain.acall({
                "question": request.question,
                "chat_history": self.memory.chat_memory.messages
            })

            # Extract sources
            sources = [
                doc.page_content[:200] + "..." 
                for doc in response["source_documents"]
            ]

            # Stream the response
            for chunk in response["answer"]:
                yield chunk

            # Update memory with the complete response
            self.memory.chat_memory.add_user_message(request.question)
            self.memory.chat_memory.add_ai_message(response["answer"])

        except Exception as e:
            raise Exception(f"Error processing chat request: {str(e)}")

# Create singleton instance
chat_service = ChatService()

async def process_chat_request(request: ChatRequest) -> AsyncGenerator[str, None]:
    """
    Process a chat request and stream the response.
    """
    async for chunk in chat_service.process_chat_request(request):
        yield chunk 