import os

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import ModelConfig
from app.models.model import ModelResponse
from app.services.model_service import model_service
from app.services.vector_store import get_vector_store

router = APIRouter()

@router.post("/configure", response_model=ModelResponse)
async def configure_model_endpoint(config: ModelConfig):
    """
    Configure the LLM model with specified parameters.
    """
    try:
        print(f"Configure model endpoint called with config: {config}")
        # Convert to dict in a way that works with both Pydantic v1 and v2
        config_dict = config.model_dump() if hasattr(config, 'model_dump') else config.dict()
        print(f"Config dict: {config_dict}")
        
        # Process model_type first if it exists
        if "model_type" in config_dict:
            model_type = config_dict["model_type"]
            # Convert ModelType enum to string if needed
            if hasattr(model_type, "value"):
                model_type = model_type.value
                config_dict["model_type"] = model_type
            
            # Set appropriate embedding type based on model type
            embedding_type = "openai" if model_type == "openai" else "huggingface"
            print(f"Setting embedding_type to {embedding_type} based on model_type {model_type}")
            
            # Update the embedding type in the config dict
            config_dict["embedding_type"] = embedding_type
        
        # Now update the full configuration
        result = model_service.update_config(config_dict)
        
        # Get the vector store and forcibly recreate it with the right embedding type
        if "embedding_type" in result:
            vector_store = get_vector_store()
            embedding_type = result["embedding_type"]
            print(f"Force updating vector store embeddings to {embedding_type}")
            
            # Force recreation regardless of current type
            vector_store._create_embeddings(embedding_type)
            vector_store.embedding_type = embedding_type
            vector_store.stores = {}  # Clear all stores
            print(f"Vector store embedding type now: {vector_store.embedding_type}")
        
        return ModelResponse(
            success=True,
            message="Model configured successfully",
            model_type=config.model_type,
            parameters=result
        )
    except Exception as e:
        print(f"Error in configure_model_endpoint: {str(e)}")
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

@router.get("/debug-embedding-type")
async def debug_embedding_type():
    """
    Debug endpoint to check the current embedding type.
    """
    try:
        vector_store = get_vector_store()
        config = model_service.get_config()
        
        return {
            "vector_store_embedding_type": vector_store.embedding_type,
            "model_service_embedding_type": config.get("embedding_type"),
            "model_type": config.get("model_type")
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting embedding type: {str(e)}"
        )

@router.post("/force-refresh-embeddings")
async def force_refresh_embeddings():
    """
    Force refresh the embedding model based on the current configuration.
    """
    try:
        config = model_service.get_config()
        embedding_type = config.get("embedding_type", "huggingface")
        
        # Get the singleton instance and force update
        vector_store = get_vector_store()
        
        # Force recreation regardless of current type
        vector_store._create_embeddings(embedding_type)
        vector_store.embedding_type = embedding_type
        vector_store.stores = {}  # Clear all stores
        
        return {
            "success": True,
            "message": f"Embedding type forcibly updated to {embedding_type}",
            "current_embedding_type": vector_store.embedding_type
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error refreshing embeddings: {str(e)}"
        )
