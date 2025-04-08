import os
from typing import Dict, Optional

from app.core.config import settings


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
            "gpu_layers": settings.DEFAULT_GPU_LAYERS,
            "embedding_type": settings.DEFAULT_EMBEDDING_TYPE
        }

    def update_config(self, config: Dict) -> Dict:
        """
        Update model configuration with new settings.
        """
        # Only print debug info if DEBUG is enabled
        if settings.DEBUG:
            print(f"update_config called with: {config}")
            print(f"Current config before update: {self.current_config}")
        
        # Validate and update configuration
        if "model_type" in config and config["model_type"] is not None:
            if config["model_type"] not in ["openai", "local"]:
                raise ValueError("Invalid model type. Must be 'openai' or 'local'")
            self.current_config["model_type"] = config["model_type"]
            
            # Automatically set embedding type based on model type if not explicitly provided
            if "embedding_type" not in config:
                embedding_type = "openai" if config["model_type"] == "openai" else "huggingface"
                if settings.DEBUG:
                    print(f"Setting embedding_type to {embedding_type} based on model_type {config['model_type']}")
                self.current_config["embedding_type"] = embedding_type

        # Batch validate numeric parameters
        numeric_params = {
            "temperature": (0, 2),
            "top_p": (0, 1),
            "repeat_penalty": (1, float('inf')),
            "max_tokens": (1, float('inf')),
            "n_ctx": (1, float('inf')),
            "gpu_layers": (-1, float('inf'))
        }

        for param, (min_val, max_val) in numeric_params.items():
            if param in config and config[param] is not None:
                if not min_val <= config[param] <= max_val:
                    raise ValueError(f"{param} must be between {min_val} and {max_val}")
                self.current_config[param] = config[param]

        if "embedding_type" in config and config["embedding_type"] is not None:
            if config["embedding_type"] not in ["huggingface", "openai"]:
                raise ValueError("Invalid embedding type. Must be 'huggingface' or 'openai'")
            self.current_config["embedding_type"] = config["embedding_type"]

        if settings.DEBUG:
            print(f"Final config after update: {self.current_config}")
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