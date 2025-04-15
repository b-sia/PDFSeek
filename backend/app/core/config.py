import os
from typing import List

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from torch.cuda import is_available

load_dotenv()

class Settings(BaseSettings):
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Model Configuration
    MODEL_DIR: str = os.getenv("MODEL_DIR", "./models")
    DEFAULT_MODEL_TYPE: str = os.getenv("DEFAULT_MODEL_TYPE", "openai")
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.1"))
    DEFAULT_MAX_TOKENS: int = int(os.getenv("DEFAULT_MAX_TOKENS", "512"))
    DEFAULT_TOP_P: float = float(os.getenv("DEFAULT_TOP_P", "0.95"))
    DEFAULT_REPEAT_PENALTY: float = float(os.getenv("DEFAULT_REPEAT_PENALTY", "1.2"))
    DEFAULT_N_CTX: int = int(os.getenv("DEFAULT_N_CTX", "4096"))
    DEFAULT_GPU_LAYERS: int = int(os.getenv("DEFAULT_GPU_LAYERS", "0" if is_available() else "-1"))

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173"]

    # Vector Store Configuration
    VECTOR_STORE_DIR: str = os.getenv("VECTOR_STORE_DIR", "./vector_store")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    DEFAULT_EMBEDDING_TYPE: str = os.getenv("DEFAULT_EMBEDDING_TYPE", "openai")

settings = Settings()