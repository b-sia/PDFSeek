import os
import asyncio
from typing import AsyncGenerator, Dict, List, Any, Optional

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.llms import LlamaCpp
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from app.core.config import settings
from app.models.chat import ChatRequest, ChatResponse
from app.services.model_service import model_service
from app.services.vector_store import get_vector_store


class ChatState(BaseModel):
    """State for the chat graph."""
    question: str
    chat_history: List[Any] = Field(default_factory=list)
    document_ids: List[str] = Field(default_factory=list)
    retrieved_docs: List[Any] = Field(default_factory=list)
    response: str = ""
    model_type: str = "openai"
    model_path: Optional[str] = None
    embedding_type: str = "openai"


class ChatService:
    def __init__(self):
        # Get the vector store instance which handles embeddings
        self.vector_store = get_vector_store()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
        )
        # Create and compile the graph
        self.graph = self._build_conversation_graph()
        # Session storage for chat histories
        self.session_histories: Dict[str, List[Any]] = {}

    def _get_llm(self, state: ChatState):
        """Get the appropriate LLM based on the state."""
        if state.model_type == "openai":
            return ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=settings.DEFAULT_TEMPERATURE,
                max_tokens=settings.DEFAULT_MAX_TOKENS,
                streaming=True
            )
        elif state.model_type == "local":
            if not state.model_path:
                raise ValueError("No local model file available. Please upload a model first or select OpenAI model type.")
            return LlamaCpp(
                model_path=state.model_path,
                temperature=settings.DEFAULT_TEMPERATURE,
                max_tokens=settings.DEFAULT_MAX_TOKENS,
                top_p=settings.DEFAULT_TOP_P,
                repeat_penalty=settings.DEFAULT_REPEAT_PENALTY,
                n_ctx=settings.DEFAULT_N_CTX,
                n_gpu_layers=settings.DEFAULT_GPU_LAYERS,
                streaming=True
            )
        else:
            raise ValueError(f"Unsupported model type: {state.model_type}")

    def _build_conversation_graph(self) -> StateGraph:
        """Build the conversation graph for processing chat requests."""
        
        def prepare_inputs(state: ChatState):
            """Prepare the initial state with the user's question."""
            # Add the user's message to chat history
            if state.chat_history is None:
                state.chat_history = []
            
            # Add user message to history
            state.chat_history.append(HumanMessage(content=state.question))
            
            return state
        
        def retrieve_documents(state: ChatState):
            """Retrieve relevant documents from the vector store."""
            # Get document content from vector store
            docs = []
            for doc_id in state.document_ids:
                doc = self.vector_store.get_document(doc_id)
                if doc:
                    docs.extend(self.text_splitter.split_text(doc))
                    
            # Create a temporary vector store for retrieval
            if docs:
                temp_vectorstore = FAISS.from_texts(docs, self.vector_store.embeddings)
                # Get relevant docs for the question
                retrieved_docs = temp_vectorstore.similarity_search(state.question, k=5)
                return {"retrieved_docs": retrieved_docs}
            
            # No documents or no relevant results
            return {"retrieved_docs": []}
        
        def generate_response(state: ChatState):
            """Generate a response using the LLM."""
            llm = self._get_llm(state)
            
            # Extract context from retrieved documents
            context = "\n\n".join([doc.page_content for doc in state.retrieved_docs])
            if not context:
                context = "No relevant information found."
            
            # Format chat history as a string for the prompt
            formatted_history = ""
            for msg in state.chat_history:
                role = "User" if isinstance(msg, HumanMessage) else "Assistant"
                formatted_history += f"{role}: {msg.content}\n"
            
            # Create prompt based on model type
            if state.model_type == "openai":
                prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are a helpful assistant. Answer the user's question based on the following context:\n\n{context}"),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{question}")
                ])
                
                # Get response
                chain = prompt | llm
                response = chain.invoke({
                    "context": context,
                    "chat_history": state.chat_history[:-1],  # Exclude the current question
                    "question": state.question
                })
                answer = response.content
            else:
                # For non-ChatOpenAI models that expect a formatted string
                template = """
                You are a helpful assistant. Answer the user's question based on the following context:
                
                {context}
                
                Chat history:
                {chat_history}
                
                User question: {question}
                
                Your answer:
                """
                
                # Get response - handle differently for non-chat models
                response = llm.invoke(template.format(
                    context=context,
                    chat_history=formatted_history,
                    question=state.question
                ))
                answer = response
            
            # Add assistant message to history
            state.chat_history.append(AIMessage(content=answer))
            state.response = answer
            
            return state
        
        # Define the workflow
        workflow = StateGraph(ChatState)
        
        # Add nodes
        workflow.add_node("prepare_inputs", prepare_inputs)
        workflow.add_node("retrieve_documents", retrieve_documents)
        workflow.add_node("generate_response", generate_response)
        
        # Set entry point
        workflow.set_entry_point("prepare_inputs")
        
        # Define edges
        workflow.add_edge("prepare_inputs", "retrieve_documents")
        workflow.add_edge("retrieve_documents", "generate_response")
        workflow.add_edge("generate_response", END)
        
        # Compile the graph
        return workflow.compile()
    
    def get_or_create_chat_history(self, session_id: str) -> List[Any]:
        """Get or create a chat history for a session."""
        if session_id not in self.session_histories:
            self.session_histories[session_id] = []
        return self.session_histories[session_id]
    
    async def process_chat_request(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Process a chat request and stream the response."""
        try:
            # Get configuration from model service
            config = model_service.get_config()
            
            # Create initial state
            initial_state = self._prepare_chat_state(request)
            
            # Determine model path for local models
            if initial_state.model_type == "local":
                model_path = None
                
                # Check request for model path
                if hasattr(request, 'model_path') and request.model_path:
                    model_path = request.model_path
                # Check config for model path
                elif 'model_path' in config and config['model_path']:
                    model_path = config['model_path']
                # Find a default model
                else:
                    # Use the first GGUF file found in the model directory as default
                    model_files = [f for f in os.listdir(settings.MODEL_DIR) if f.endswith('.gguf')]
                    if model_files:
                        model_path = os.path.join(settings.MODEL_DIR, model_files[0])
                    else:
                        raise ValueError("No local model files found. Please upload a model first.")
                
                # Update model path in state
                initial_state.model_path = model_path
            
            # Process through the graph
            final_state = self.graph.invoke(initial_state)
            
            # Store the updated chat history
            self.session_histories[request.session_id] = final_state["chat_history"]
            
            # Stream the response (in this case it's just one chunk, but could be adapted for true streaming)
            yield final_state["response"]
            
        except Exception as e:
            raise Exception(f"Error processing chat request: {str(e)}")

    def _prepare_chat_state(self, request: ChatRequest) -> ChatState:
        """Prepare chat state from request and model configuration."""
        config = model_service.get_config()
        
        # Set the model_type from the config
        model_type = config.get("model_type", "openai")
        
        # Ensure embedding_type matches model_type
        if "embedding_type" not in config or config["embedding_type"] is None:
            config["embedding_type"] = "openai" if model_type == "openai" else "huggingface"
        
        # Update embedding type in vector store
        self.vector_store.update_embeddings(config["embedding_type"])
        
        # Get model path if available
        model_path = config.get("model_path")
            
        return ChatState(
            question=request.question,
            chat_history=self.session_histories.get(request.session_id, []),
            document_ids=request.document_ids,
            model_type=model_type,
            model_path=model_path,  # This can be None now
            embedding_type=config["embedding_type"]
        )


# Create singleton instance
chat_service = ChatService()

async def process_chat_request(request: ChatRequest) -> AsyncGenerator[str, None]:
    """
    Process a chat request and stream the response.
    Entry point function that uses the singleton instance.
    """
    async for chunk in chat_service.process_chat_request(request):
        yield chunk 