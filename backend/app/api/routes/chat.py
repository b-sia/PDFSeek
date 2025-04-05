from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import process_chat_request
from app.services.session_service import session_service

router = APIRouter()

# Dependency to get session
async def get_session():
    session_id = session_service.create_session()
    return session_id

@router.post("/stream", response_model=ChatResponse)
async def chat_stream(
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
            
        # If document IDs are not provided in the request, use the ones from the session
        if not request.document_ids and session_data.get("document_ids"):
            request.document_ids = session_data["document_ids"]

        async def generate() -> AsyncGenerator[str, None]:
            async for chunk in process_chat_request(request):
                yield chunk

        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )
