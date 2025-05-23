from typing import Dict, List

import uvicorn
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.models.schemas import ChatRequest, ChatResponse, ModelConfig
from app.services.chat_service import process_chat_request
from app.services.error_service import error_service
from app.services.model_service import model_service
from app.services.pdf_service import process_pdfs
from app.services.session_service import session_service

from app.api.routes import model
from app.api.routes import pdf
from app.api.routes import chat

app = FastAPI(
    title="PDF Chat API",
    description="API for chatting with PDF documents using various LLM models",
    version="1.0.0"
)

app.include_router(model.router, prefix="/api/model", tags=["model"])
app.include_router(pdf.router, prefix="/api/pdf", tags=["pdf"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get session
async def get_session():
    session_id = session_service.create_session()
    return session_id

@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    session_id: str = Depends(get_session)
):
    """
    Process a chat request and stream the response.
    """
    try:
        # Get session data
        session_data = session_service.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        # Process chat request
        async def generate():
            async for chunk in process_chat_request(request, session_data["document_ids"]):
                yield chunk

        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception as e:
        raise error_service.handle_error(e, context="Chat processing failed")

@app.get("/api/session/{session_id}")
async def get_session_data(session_id: str):
    """
    Get session data.
    """
    try:
        session_data = session_service.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        return session_data
    except Exception as e:
        raise error_service.handle_error(e, context="Failed to get session data")

@app.post("/api/session/create")
async def create_session():
    """
    Create a new session and return its ID.
    """
    try:
        session_id = session_service.create_session()
        return {"session_id": session_id}
    except Exception as e:
        raise error_service.handle_error(e, context="Failed to create session")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
