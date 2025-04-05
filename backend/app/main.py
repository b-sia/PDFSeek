from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List, Dict
import uvicorn
from app.core.config import settings
from app.services.pdf_service import process_pdfs
from app.services.chat_service import process_chat_request
from app.services.model_service import model_service
from app.services.error_service import error_service
from app.services.session_service import session_service
from app.models.schemas import ChatRequest, ModelConfig, ChatResponse

app = FastAPI(
    title="PDF Chat API",
    description="API for chatting with PDF documents using various LLM models",
    version="1.0.0"
)

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

@app.post("/api/upload")
async def upload_pdfs(
    files: List[UploadFile] = File(...),
    session_id: str = Depends(get_session)
):
    """
    Upload and process PDF files.
    """
    try:
        result = await process_pdfs(files)
        for doc_id in result["document_ids"]:
            session_service.add_document_to_session(session_id, doc_id)
        return result
    except Exception as e:
        raise error_service.handle_error(e, context="PDF upload failed")

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

@app.post("/api/model/config")
async def update_model_config(
    config: ModelConfig,
    session_id: str = Depends(get_session)
):
    """
    Update model configuration.
    """
    try:
        updated_config = model_service.update_config(config.dict())
        session_service.update_session(session_id, {"model_config": updated_config})
        return updated_config
    except Exception as e:
        raise error_service.handle_error(e, context="Model configuration update failed")

@app.get("/api/model/config")
async def get_model_config(session_id: str = Depends(get_session)):
    """
    Get current model configuration.
    """
    try:
        return model_service.get_config()
    except Exception as e:
        raise error_service.handle_error(e, context="Failed to get model configuration")

@app.post("/api/model/upload")
async def upload_local_model(
    model_file: UploadFile = File(...),
    session_id: str = Depends(get_session)
):
    """
    Upload a local LLM model file.
    """
    try:
        model_path = model_service.upload_local_model(
            await model_file.read(),
            model_file.filename
        )
        return {"model_path": model_path}
    except Exception as e:
        raise error_service.handle_error(e, context="Model upload failed")

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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
