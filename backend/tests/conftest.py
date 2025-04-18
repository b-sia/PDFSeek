import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.services.session_service import SessionService
from app.services.chat_service import ChatService
from app.models.chat import ChatRequest, ChatResponse
from app.services.vector_store import VectorStore
from app.core.config import settings


# Set TESTING environment variable for all tests
os.environ["TESTING"] = "true"


# Configure pytest to skip tests that require model loading
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "requires_model: mark test as requiring actual model loading"
    )


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def set_debug_mode():
    """Set DEBUG mode to True for testing."""
    # Store the original value
    original_debug = settings.DEBUG
    
    # Set DEBUG to True
    settings.DEBUG = True
    
    yield
    
    # Restore the original value
    settings.DEBUG = original_debug


@pytest.fixture(autouse=True)
def mock_openai_api_key():
    """Mock the OpenAI API key to prevent authentication errors."""
    # Store the original value
    original_key = settings.OPENAI_API_KEY
    
    # Set a test value
    settings.OPENAI_API_KEY = "test-api-key"
    
    yield
    
    # Restore the original value
    settings.OPENAI_API_KEY = original_key


@pytest.fixture(autouse=True)
def mock_vector_store_embeddings():
    """Mock the vector store's _create_embeddings method to prevent OpenAI API calls."""
    with patch("app.services.vector_store.VectorStore._create_embeddings") as mock:
        # Create a mock embeddings object
        mock_embeddings = MagicMock()
        # Set up the embed_documents method to return mock embeddings
        mock_embeddings.embed_documents.return_value = [[0.1, 0.2, 0.3]]
        # Set up other required methods/attributes
        mock_embeddings.embed_query.return_value = [0.1, 0.2, 0.3]
        mock.return_value = mock_embeddings
        yield mock


@pytest.fixture(autouse=True)
def mock_get_llm():
    """Mock the _get_llm method to prevent model loading."""
    with patch("app.services.chat_service.ChatService._get_llm") as mock:
        mock.return_value = MagicMock()
        yield mock


@pytest.fixture
def mock_session_service():
    """Create a mock session service."""
    with patch("app.services.session_service.session_service") as mock:
        # Configure the mock to return a session ID
        mock.create_session.return_value = "test-session-id"
        
        # Configure the mock to return session data
        mock.get_session.return_value = {
            "created_at": "2023-01-01T00:00:00",
            "last_accessed": "2023-01-01T00:00:00",
            "document_ids": ["doc1", "doc2"],
            "chat_history": [],
            "model_config": {}
        }
        
        yield mock


@pytest.fixture
def mock_chat_service():
    """Create a mock chat service."""
    with patch("app.services.chat_service.process_chat_request") as mock:
        # Configure the mock to return a generator that yields a response
        async def mock_generator():
            yield "This is a test response"
        
        mock.return_value = mock_generator()
        yield mock


@pytest.fixture
def sample_chat_request():
    """Create a sample chat request."""
    return ChatRequest(
        question="What is the capital of France?",
        model_type="openai",
        session_id="test-session-id",
        document_ids=["doc1", "doc2"]
    )


@pytest.fixture
def sample_chat_response():
    """Create a sample chat response."""
    return ChatResponse(
        answer="The capital of France is Paris.",
        sources=["doc1"],
        tokens_used=10,
        model_type="openai"
    ) 