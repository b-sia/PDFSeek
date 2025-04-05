import logging
from typing import Optional
from fastapi import HTTPException
import traceback
import os
from datetime import datetime

class ErrorService:
    def __init__(self):
        # Set up logging
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        log_file = os.path.join(self.log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("pdf_chat")

    def log_error(self, error: Exception, context: Optional[str] = None):
        """
        Log an error with context and stack trace.
        """
        error_message = f"Error: {str(error)}"
        if context:
            error_message = f"{context} - {error_message}"
        
        self.logger.error(error_message)
        self.logger.error(traceback.format_exc())

    def handle_error(self, error: Exception, status_code: int = 500, context: Optional[str] = None) -> HTTPException:
        """
        Handle an error and return an HTTPException.
        """
        self.log_error(error, context)
        
        error_message = str(error)
        if context:
            error_message = f"{context}: {error_message}"
            
        return HTTPException(
            status_code=status_code,
            detail=error_message
        )

    def log_info(self, message: str):
        """
        Log an informational message.
        """
        self.logger.info(message)

    def log_warning(self, message: str):
        """
        Log a warning message.
        """
        self.logger.warning(message)

# Create singleton instance
error_service = ErrorService() 