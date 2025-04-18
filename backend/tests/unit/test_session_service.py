import os
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open, MagicMock

from app.services.session_service import SessionService


class TestSessionService:
    """Test cases for the SessionService class."""
    
    @pytest.fixture
    def session_service(self, tmp_path):
        """Create a SessionService instance with a temporary directory."""
        with patch("app.services.session_service.SessionService.__init__") as mock_init:
            mock_init.return_value = None
            service = SessionService()
            service.sessions_dir = str(tmp_path)
            service.session_timeout = timedelta(hours=24)
            return service
    
    def test_get_session_path(self, session_service):
        """Test getting the session file path."""
        session_id = "test-session-id"
        expected_path = os.path.join(session_service.sessions_dir, f"{session_id}.json")
        assert session_service._get_session_path(session_id) == expected_path
    
    def test_create_session(self, session_service):
        """Test creating a new session."""
        with patch("uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = "test-session-id"
            
            mock_file = MagicMock()
            mock_write = MagicMock()
            mock_file.__enter__.return_value = mock_write
            
            with patch("builtins.open", return_value=mock_file):
                session_id = session_service.create_session()
                
                # Check that the session ID is returned
                assert session_id == "test-session-id"
                
                # Check that the file was written with valid JSON data
                write_calls = mock_write.write.call_args_list
                written_json = "".join(call[0][0] for call in write_calls)
                session_data = json.loads(written_json)
                
                assert "created_at" in session_data
                assert "last_accessed" in session_data
                assert session_data["document_ids"] == []
                assert session_data["chat_history"] == []
                assert session_data["model_config"] == {}
    
    def test_get_session_not_found(self, session_service):
        """Test getting a non-existent session."""
        session_id = "non-existent-session"
        
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False
            
            result = session_service.get_session(session_id)
            
            # Check that None was returned
            assert result is None
    
    def test_get_session_expired(self, session_service):
        """Test getting an expired session."""
        session_id = "expired-session"
        session_path = session_service._get_session_path(session_id)
        
        # Create a mock session file with an expired last_accessed time
        expired_time = (datetime.now() - timedelta(hours=25)).isoformat()
        session_data = {
            "created_at": datetime.now().isoformat(),
            "last_accessed": expired_time,
            "document_ids": ["doc1", "doc2"],
            "chat_history": [],
            "model_config": {}
        }
        
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            
            mock_file = mock_open(read_data=json.dumps(session_data))
            
            with patch("builtins.open", mock_file):
                with patch.object(session_service, "delete_session") as mock_delete:
                    result = session_service.get_session(session_id)
                    
                    # Check that the file was opened for reading
                    mock_file.assert_called_once_with(session_path, "r")
                    
                    # Check that delete_session was called
                    mock_delete.assert_called_once_with(session_id)
                    
                    # Check that None was returned
                    assert result is None
    
    def test_update_session(self, session_service):
        """Test updating session data."""
        session_id = "test-session-id"
        
        # Mock get_session to return existing session data
        existing_data = {
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "document_ids": ["doc1"],
            "chat_history": [],
            "model_config": {}
        }
        
        updates = {
            "document_ids": ["doc1", "doc2"]
        }
        
        with patch.object(session_service, "get_session") as mock_get:
            mock_get.return_value = existing_data
            
            mock_file = MagicMock()
            mock_write = MagicMock()
            mock_file.__enter__.return_value = mock_write
            
            with patch("builtins.open", return_value=mock_file):
                result = session_service.update_session(session_id, updates)
                
                # Check that get_session was called
                mock_get.assert_called_once_with(session_id)
                
                # Check that the file was written with valid JSON data
                write_calls = mock_write.write.call_args_list
                written_json = "".join(call[0][0] for call in write_calls)
                updated_data = json.loads(written_json)
                
                assert updated_data["document_ids"] == ["doc1", "doc2"]
                assert "last_accessed" in updated_data
                
                # Check that the updated data was returned
                assert result == updated_data
    
    def test_update_session_not_found(self, session_service):
        """Test updating a non-existent session."""
        session_id = "non-existent-session"
        updates = {"document_ids": ["doc1"]}
        
        with patch.object(session_service, "get_session") as mock_get:
            mock_get.return_value = None
            
            with pytest.raises(ValueError, match="Session not found or expired"):
                session_service.update_session(session_id, updates)
    
    def test_add_document_to_session(self, session_service):
        """Test adding a document to a session."""
        session_id = "test-session-id"
        document_id = "doc3"
        
        # Mock get_session to return existing session data
        existing_data = {
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "document_ids": ["doc1", "doc2"],
            "chat_history": [],
            "model_config": {}
        }
        
        with patch.object(session_service, "get_session") as mock_get:
            mock_get.return_value = existing_data
            
            with patch.object(session_service, "update_session") as mock_update:
                result = session_service.add_document_to_session(session_id, document_id)
                
                # Check that get_session was called
                mock_get.assert_called_once_with(session_id)
                
                # Check that update_session was called with the updated document_ids
                mock_update.assert_called_once()
                update_args = mock_update.call_args[0]
                assert update_args[0] == session_id
                assert "document_ids" in update_args[1]
                assert document_id in update_args[1]["document_ids"]
                
                # Check that the updated document_ids were returned
                assert result == ["doc1", "doc2", "doc3"]
    
    def test_add_document_to_session_already_exists(self, session_service):
        """Test adding a document that already exists in the session."""
        session_id = "test-session-id"
        document_id = "doc1"  # Already exists
        
        # Mock get_session to return existing session data
        existing_data = {
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "document_ids": ["doc1", "doc2"],
            "chat_history": [],
            "model_config": {}
        }
        
        with patch.object(session_service, "get_session") as mock_get:
            mock_get.return_value = existing_data
            
            with patch.object(session_service, "update_session") as mock_update:
                result = session_service.add_document_to_session(session_id, document_id)
                
                # Check that get_session was called
                mock_get.assert_called_once_with(session_id)
                
                # Check that update_session was not called (document already exists)
                mock_update.assert_not_called()
                
                # Check that the original document_ids were returned
                assert result == ["doc1", "doc2"]
    
    def test_delete_session(self, session_service):
        """Test deleting a session."""
        session_id = "test-session-id"
        session_path = session_service._get_session_path(session_id)
        
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            
            with patch("os.remove") as mock_remove:
                result = session_service.delete_session(session_id)
                
                # Check that os.path.exists was called
                mock_exists.assert_called_once_with(session_path)
                
                # Check that os.remove was called
                mock_remove.assert_called_once_with(session_path)
                
                # Check that True was returned
                assert result is True
    
    def test_delete_session_not_found(self, session_service):
        """Test deleting a non-existent session."""
        session_id = "non-existent-session"
        session_path = session_service._get_session_path(session_id)
        
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False
            
            with patch("os.remove") as mock_remove:
                result = session_service.delete_session(session_id)
                
                # Check that os.path.exists was called
                mock_exists.assert_called_once_with(session_path)
                
                # Check that os.remove was not called
                mock_remove.assert_not_called()
                
                # Check that False was returned
                assert result is False 