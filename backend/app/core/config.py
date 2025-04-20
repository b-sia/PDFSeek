import os
from typing import List

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from torch.cuda import is_available

load_dotenv()

# Debug CUDA environment
print("CUDA Environment Check:")
print(f"CUDA_VISIBLE_DEVICES: {os.getenv('CUDA_VISIBLE_DEVICES', 'Not set')}")
print(f"CUDA available: {is_available()}")
if is_available():
    import torch
    print(f"CUDA device count: {torch.cuda.device_count()}")
    print(f"Current CUDA device: {torch.cuda.current_device()}")
    print(f"CUDA device name: {torch.cuda.get_device_name()}")

class Settings(BaseSettings):
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Model Configuration
    MODEL_DIR: str = os.getenv("MODEL_DIR", "./models")
    MODEL_TYPE: str = os.getenv("MODEL_TYPE", "openai")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "512"))
    TOP_P: float = float(os.getenv("TOP_P", "0.95"))
    REPEAT_PENALTY: float = float(os.getenv("REPEAT_PENALTY", "1.2"))
    N_CTX: int = int(os.getenv("N_CTX", "4096"))
    GPU_LAYERS: int = int(os.getenv("GPU_LAYERS", "32" if is_available() else "-1"))

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # CORS Configuration
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    # Vector Store Configuration
    VECTOR_STORE_DIR: str = os.getenv("VECTOR_STORE_DIR", "./vector_store")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    EMBEDDING_TYPE: str = os.getenv("EMBEDDING_TYPE", "openai")

settings = Settings()