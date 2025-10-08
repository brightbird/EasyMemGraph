import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the memory agent."""

    @staticmethod
    def get_model_config() -> Dict[str, Any]:
        """Get ModelScope LLM configuration."""
        return {
            "provider": "openai",
            "config": {
                "model": os.getenv("MODEL_NAME", "deepseek-ai/DeepSeek-V3.1"),
                "temperature": float(os.getenv("MODEL_TEMPERATURE", "0.2")),
                "max_tokens": int(os.getenv("MODEL_MAX_TOKENS", "2000")),
                "api_key": os.getenv("MODELSCOPE_API_KEY"),
                "openai_base_url": os.getenv("MODELSCOPE_BASE_URL", "https://api-inference.modelscope.cn/v1")
            }
        }

    @staticmethod
    def get_embedding_config() -> Dict[str, Any]:
        """Get embedding model configuration using local huggingface."""
        return {
            "provider": "huggingface",
            "config": {
                "model": os.getenv("EMBEDDING_MODEL", "moka-ai/m3e-base"),
                "model_kwargs": {
                    "device": "cpu",  # Change to "cuda" if GPU is available
                    "trust_remote_code": True
                }
            }
        }

    @staticmethod
    def get_qdrant_config() -> Dict[str, Any]:
        """Get Qdrant vector store configuration."""
        return {
            "provider": "qdrant",
            "config": {
                "collection_name": os.getenv("QDRANT_COLLECTION_NAME", "conversation_memories"),
                "embedding_model_dims": int(os.getenv("EMBEDDING_DIMS", "768")),
                "url": os.getenv("QDRANT_URL", "http://localhost:6333"),
                "api_key": os.getenv("QDRANT_API_KEY", None) or None
            }
        }

    @staticmethod
    def get_mem0_config() -> Dict[str, Any]:
        """Get complete Mem0 configuration."""
        return {
            "llm": Config.get_model_config(),
            "embedder": Config.get_embedding_config(),
            "vector_store": Config.get_qdrant_config(),
            "version": os.getenv("MEMORY_VERSION", "v1.1")
        }

    @staticmethod
    def get_langsmith_config() -> Dict[str, str]:
        """Get LangSmith configuration for tracing."""
        return {
            "LANGCHAIN_TRACING_V2": os.getenv("LANGCHAIN_TRACING_V2", "true"),
            "LANGCHAIN_ENDPOINT": os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"),
            "LANGCHAIN_API_KEY": os.getenv("LANGCHAIN_API_KEY"),
            "LANGCHAIN_PROJECT": os.getenv("LANGCHAIN_PROJECT", "EasyMemGraph")
        }

    @staticmethod
    def get_env_variables() -> Dict[str, str]:
        """Get all environment variables for the application."""
        env_vars = {
            "OPENAI_API_KEY": os.getenv("MODELSCOPE_API_KEY"),
            "OPENAI_BASE_URL": os.getenv("MODELSCOPE_BASE_URL", "https://api.modelscope.cn/v1"),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO")
        }

        # Add LangSmith environment variables
        langsmith_config = Config.get_langsmith_config()
        env_vars.update(langsmith_config)

        return env_vars