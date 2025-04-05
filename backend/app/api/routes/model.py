import os

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import ModelConfig
from app.models.model import ModelResponse
from app.services.model_service import model_service

router = APIRouter()

@router.post("/configure", response_model=ModelResponse)
async def configure_model_endpoint(config: ModelConfig):
    """
    Configure the LLM model with specified parameters.
    """
    try:
        # Convert to dict in a way that works with both Pydantic v1 and v2
        config_dict = config.model_dump() if hasattr(config, 'model_dump') else config.dict()
        result = model_service.update_config(config_dict)
        return ModelResponse(
            success=True,
            message="Model configured successfully",
            model_type=config.model_type,
            parameters=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error configuring model: {str(e)}"
        )

@router.post("/upload-local")
async def upload_model_endpoint(file: UploadFile = File(...)):
    """
    Upload a local GGUF model file.
    """
    try:
        file_content = await file.read()
        model_path = model_service.upload_local_model(file_content, file.filename)
        return {
            "success": True,
            "message": "Model uploaded successfully",
            "model_path": model_path
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading model: {str(e)}"
        )
