import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.chat import ChatRequest


class TestChatRoutes:
    """Test cases for the chat API routes."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_chat_request(self):
        """Create a sample chat request."""
        return {
            "question": "What is the capital of France?",
            "model_type": "openai",
            "session_id": "test-session-id",
            "document_ids": ["doc1", "doc2"]
        }
    
    def test_chat_stream(self, client, sample_chat_request):
        """Test the chat stream endpoint."""
        # Mock the session service
        with patch("app.api.routes.chat.session_service") as mock_session_service:
            # Configure the mock to return session data
            mock_session_service.get_session.return_value = {
                "created_at": "2023-01-01T00:00:00",
                "last_accessed": "2023-01-01T00:00:00",
                "document_ids": ["doc1", "doc2"],
                "chat_history": [],
                "model_config": {}
            }
            
            # Mock the process_chat_request function
            with patch("app.api.routes.chat.process_chat_request") as mock_process:
                # Configure the mock to return a generator that yields a response
                async def mock_generator():
                    yield "This is a test response"
                
                mock_process.return_value = mock_generator()
                
                # Make the request
                response = client.post("/api/chat/stream", json=sample_chat_request)
                
                # Check that the response status code is 200
                assert response.status_code == 200
                
                # Check that the response content type is text/event-stream
                assert response.headers["content-type"].startswith("text/event-stream")
                
                # Check that the response content contains the expected text
                assert "This is a test response" in response.text
    
    def test_chat_stream_session_not_found(self, client, sample_chat_request):
        """Test the chat stream endpoint when the session is not found."""
        # Mock the session service
        with patch("app.api.routes.chat.session_service") as mock_session_service:
            # Configure the mock to return None (session not found)
            mock_session_service.get_session.return_value = None
            
            # Make the request
            response = client.post("/api/chat/stream", json=sample_chat_request)
            
            # Check that the response status code is 404
            assert response.status_code == 404
            
            # Check that the response contains the expected error message
            assert "Session not found" in response.json()["detail"] 