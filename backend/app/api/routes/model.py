import os

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.model import ModelConfig, ModelResponse
from app.services.model_service import configure_model, upload_local_model

router = APIRouter()

@router.post("/configure", response_model=ModelResponse)
async def configure_model_endpoint(config: ModelConfig):
    """
    Configure the LLM model with specified parameters.
    """
    try:
        result = await configure_model(config)
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
        model_path = await upload_local_model(file)
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
