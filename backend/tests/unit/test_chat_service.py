import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.messages import HumanMessage, AIMessage
import os

from app.services.chat_service import ChatService, ChatState
from app.models.chat import ChatRequest


class TestChatService:
    """Test cases for the ChatService class."""
    
    @pytest.fixture
    def chat_service(self):
        """Create a ChatService instance with mocked dependencies."""
        with patch("app.services.chat_service.get_vector_store") as mock_vector_store:
            with patch("app.services.chat_service.RecursiveCharacterTextSplitter") as mock_splitter:
                with patch("app.services.chat_service.StateGraph") as mock_graph:
                    # Configure the mocks
                    mock_vector_store.return_value = MagicMock()
                    mock_splitter.return_value = MagicMock()
                    mock_graph.return_value = MagicMock()
                    
                    # Create the service
                    service = ChatService()
                    
                    # Mock the graph
                    service.graph = MagicMock()
                    service.graph.compile.return_value = MagicMock()
                    
                    yield service
    
    @pytest.fixture
    def sample_chat_request(self):
        """Create a sample chat request."""
        return ChatRequest(
            question="What is the capital of France?",
            model_type="openai",
            session_id="test-session-id",
            document_ids=["doc1", "doc2"]
        )
    
    def test_infer_model_type_from_path(self, chat_service):
        """Test inferring model type from file path."""
        # Test GGUF model
        assert chat_service._infer_model_type_from_path("model.gguf") == "llama"
        
        # Test safetensors model
        assert chat_service._infer_model_type_from_path("model.safetensors") == "safetensors"
        
        # Test PyTorch model
        assert chat_service._infer_model_type_from_path("model.pt") == "pytorch"
        assert chat_service._infer_model_type_from_path("model.pth") == "pytorch"
        assert chat_service._infer_model_type_from_path("model.bin") == "pytorch"
        
        # Test unsupported model
        with pytest.raises(ValueError, match="Unsupported model file extension"):
            chat_service._infer_model_type_from_path("model.xyz")
    
    @pytest.mark.asyncio
    async def test_prepare_chat_state(self, chat_service, sample_chat_request):
        """Test preparing chat state from a request."""
        state = chat_service._prepare_chat_state(sample_chat_request)
        
        # Check that the state was created correctly
        assert state.question == sample_chat_request.question
        assert state.model_type == sample_chat_request.model_type
        assert state.model_path == sample_chat_request.model_path
        assert state.document_ids == sample_chat_request.document_ids
        assert state.chat_history == []
        assert state.retrieved_docs == []
        assert state.response == ""
    
    @pytest.mark.asyncio
    async def test_get_or_create_chat_history(self, chat_service):
        """Test getting or creating chat history."""
        session_id = "test-session-id"
        
        # Test getting existing chat history
        chat_service.session_histories[session_id] = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!")
        ]
        
        history = chat_service.get_or_create_chat_history(session_id)
        
        assert history == chat_service.session_histories[session_id]
        
        # Test creating new chat history
        new_session_id = "new-session-id"
        new_history = chat_service.get_or_create_chat_history(new_session_id)
        
        assert new_history == []
        assert new_session_id in chat_service.session_histories
        assert chat_service.session_histories[new_session_id] == [] 