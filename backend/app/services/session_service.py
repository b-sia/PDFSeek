import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class SessionService:
    def __init__(self):
        self.sessions_dir = "sessions"
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)
        self.session_timeout = timedelta(hours=24)  # 24-hour session timeout

    def _get_session_path(self, session_id: str) -> str:
        """
        Get the file path for a session.
        """
        return os.path.join(self.sessions_dir, f"{session_id}.json")

    def _safe_json_load(self, file_path: str) -> Optional[Dict]:
        """
        Safely load JSON data from a file.
        """
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from {file_path}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error reading session file {file_path}: {str(e)}")
            return None

    def _safe_json_dump(self, data: Dict, file_path: str) -> bool:
        """
        Safely write JSON data to a file.
        """
        try:
            with open(file_path, "w") as f:
                json.dump(data, f)
            return True
        except Exception as e:
            logger.error(f"Error writing session file {file_path}: {str(e)}")
            return False

    def create_session(self) -> str:
        """
        Create a new session and return its ID.
        """
        session_id = str(uuid.uuid4())
        session_data = {
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "document_ids": [],
            "chat_history": [],
            "model_config": {}
        }
        
        if not self._safe_json_dump(session_data, self._get_session_path(session_id)):
            raise ValueError("Failed to create session file")
            
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session data if it exists and is not expired.
        """
        session_path = self._get_session_path(session_id)
        if not os.path.exists(session_path):
            return None

        session_data = self._safe_json_load(session_path)
        if not session_data:
            return None

        try:
            # Check if session is expired
            last_accessed = datetime.fromisoformat(session_data["last_accessed"])
            if datetime.now() - last_accessed > self.session_timeout:
                self.delete_session(session_id)
                return None

            # Update last accessed time
            session_data["last_accessed"] = datetime.now().isoformat()
            if not self._safe_json_dump(session_data, session_path):
                logger.error(f"Failed to update last accessed time for session {session_id}")
                return None

            return session_data
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid session data format for {session_id}: {str(e)}")
            return None

    def update_session(self, session_id: str, updates: Dict) -> Dict:
        """
        Update session data with new information.
        """
        session_data = self.get_session(session_id)
        if not session_data:
            raise ValueError("Session not found or expired")

        session_data.update(updates)
        session_data["last_accessed"] = datetime.now().isoformat()

        if not self._safe_json_dump(session_data, self._get_session_path(session_id)):
            raise ValueError("Failed to update session file")

        return session_data

    def add_document_to_session(self, session_id: str, document_id: str) -> List[str]:
        """
        Add a document ID to the session's document list.
        """
        session_data = self.get_session(session_id)
        if not session_data:
            raise ValueError("Session not found or expired")

        if document_id not in session_data["document_ids"]:
            session_data["document_ids"].append(document_id)
            self.update_session(session_id, session_data)

        return session_data["document_ids"]

    def add_chat_message(self, session_id: str, message: Dict) -> List[Dict]:
        """
        Add a chat message to the session's chat history.
        """
        session_data = self.get_session(session_id)
        if not session_data:
            raise ValueError("Session not found or expired")

        session_data["chat_history"].append(message)
        self.update_session(session_id, session_data)

        return session_data["chat_history"]

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and its associated data.
        """
        session_path = self._get_session_path(session_id)
        if os.path.exists(session_path):
            try:
                os.remove(session_path)
                return True
            except Exception as e:
                logger.error(f"Error deleting session file {session_path}: {str(e)}")
                return False
        return False

    def cleanup_expired_sessions(self):
        """
        Remove all expired sessions.
        """
        for filename in os.listdir(self.sessions_dir):
            if filename.endswith(".json"):
                session_id = filename[:-5]  # Remove .json extension
                self.get_session(session_id)  # This will delete expired sessions

# Create singleton instance
session_service = SessionService() 