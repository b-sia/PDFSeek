from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import process_chat_request

router = APIRouter()

@router.post("/stream", response_model=ChatResponse)
async def chat_stream(request: ChatRequest):
    """
    Process a chat request and stream the response.
    """
    try:
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
