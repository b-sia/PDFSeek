from typing import Dict, Optional
from app.core.config import settings
import os

class ModelService:
    def __init__(self):
        self.model_dir = settings.MODEL_DIR
        self.current_config = {
            "model_type": settings.DEFAULT_MODEL_TYPE,
            "temperature": settings.DEFAULT_TEMPERATURE,
            "max_tokens": settings.DEFAULT_MAX_TOKENS,
            "top_p": settings.DEFAULT_TOP_P,
            "repeat_penalty": settings.DEFAULT_REPEAT_PENALTY,
            "n_ctx": settings.DEFAULT_N_CTX,
            "gpu_layers": settings.DEFAULT_GPU_LAYERS
        }

    def update_config(self, config: Dict) -> Dict:
        """
        Update model configuration with new settings.
        """
        # Validate and update configuration
        if "model_type" in config:
            if config["model_type"] not in ["openai", "local"]:
                raise ValueError("Invalid model type. Must be 'openai' or 'local'")
            self.current_config["model_type"] = config["model_type"]

        if "temperature" in config:
            if not 0 <= config["temperature"] <= 2:
                raise ValueError("Temperature must be between 0 and 2")
            self.current_config["temperature"] = config["temperature"]

        if "max_tokens" in config:
            if config["max_tokens"] < 1:
                raise ValueError("Max tokens must be greater than 0")
            self.current_config["max_tokens"] = config["max_tokens"]

        if "top_p" in config:
            if not 0 <= config["top_p"] <= 1:
                raise ValueError("Top p must be between 0 and 1")
            self.current_config["top_p"] = config["top_p"]

        if "repeat_penalty" in config:
            if config["repeat_penalty"] < 1:
                raise ValueError("Repeat penalty must be greater than or equal to 1")
            self.current_config["repeat_penalty"] = config["repeat_penalty"]

        if "n_ctx" in config:
            if config["n_ctx"] < 1:
                raise ValueError("Context window must be greater than 0")
            self.current_config["n_ctx"] = config["n_ctx"]

        if "gpu_layers" in config:
            if config["gpu_layers"] < 0:
                raise ValueError("GPU layers must be greater than or equal to 0")
            self.current_config["gpu_layers"] = config["gpu_layers"]

        return self.current_config

    def get_config(self) -> Dict:
        """
        Get current model configuration.
        """
        return self.current_config

    def upload_local_model(self, model_file: bytes, filename: str) -> str:
        """
        Upload and save a local LLM model file.
        """
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)

        model_path = os.path.join(self.model_dir, filename)
        with open(model_path, "wb") as f:
            f.write(model_file)

        return model_path

# Create singleton instance
model_service = ModelService() 