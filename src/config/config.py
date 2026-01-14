"""Configuration module for managing environment variables and application settings."""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Config:
    """Centralized configuration management for the application.

    This class loads and provides access to all environment variables
    needed for the application to function.
    """

    # Prompts (defined as class variable as it doesn't depend on env vars)
    PROMPT_DEFINITION: str = """
Please review the following document content and determine if it is of low quality or high quality.
Low quality means the content contains many meaningless or unrelated words or sentences.
High quality means the content is clear, organized, and meaningful.
Step-by-step evaluation process:
1. Check for basic quality indicators such as grammar and coherence.
2. Assess the overall organization and meaningfulness of the content.
3. Make a final quality determination based on the above criteria.
Respond strictly with "low quality" or "high quality".
Content:
"""

    @classmethod
    def api_url(cls) -> str:
        """Get API URL from environment."""
        return os.getenv("API_URL")

    @classmethod
    def api_token(cls) -> str:
        """Get API token from environment."""
        return os.getenv("API_TOKEN")

    @classmethod
    def ollama_url(cls) -> str:
        """Get Ollama URL from environment."""
        return os.getenv("OLLAMA_URL")

    @classmethod
    def ollama_endpoint(cls) -> str:
        """Get Ollama endpoint from environment."""
        return os.getenv("OLLAMA_ENDPOINT")

    @classmethod
    def model_name(cls) -> str:
        """Get primary model name from environment."""
        return os.getenv("MODEL_NAME")

    @classmethod
    def second_model_name(cls) -> Optional[str]:
        """Get secondary model name from environment."""
        return os.getenv("SECOND_MODEL_NAME")

    @classmethod
    def third_model_name(cls) -> Optional[str]:
        """Get tertiary model name from environment."""
        return os.getenv("THIRD_MODEL_NAME")

    @classmethod
    def num_llm_models(cls) -> int:
        """Get number of LLM models to use from environment."""
        return int(os.getenv("NUM_LLM_MODELS", "3"))

    @classmethod
    def low_quality_tag_id(cls) -> int:
        """Get low quality tag ID from environment."""
        return int(os.getenv("LOW_QUALITY_TAG_ID"))

    @classmethod
    def high_quality_tag_id(cls) -> int:
        """Get high quality tag ID from environment."""
        return int(os.getenv("HIGH_QUALITY_TAG_ID"))

    @classmethod
    def max_documents(cls) -> int:
        """Get maximum documents to process from environment."""
        return int(os.getenv("MAX_DOCUMENTS"))

    @classmethod
    def rename_documents(cls) -> bool:
        """Get whether to rename documents from environment."""
        return os.getenv("RENAME_DOCUMENTS", "no").lower() == 'yes'

    @classmethod
    def log_level(cls) -> str:
        """Get log level from environment."""
        return LOG_LEVEL

    @classmethod
    def validate(cls) -> None:
        """Validate that all required configuration values are present.

        Raises:
            ValueError: If any required configuration value is missing or invalid.
        """
        required_vars = {
            "API_URL": cls.api_url(),
            "API_TOKEN": cls.api_token(),
            "OLLAMA_URL": cls.ollama_url(),
            "OLLAMA_ENDPOINT": cls.ollama_endpoint(),
            "MODEL_NAME": cls.model_name(),
            "LOW_QUALITY_TAG_ID": cls.low_quality_tag_id(),
            "HIGH_QUALITY_TAG_ID": cls.high_quality_tag_id(),
            "MAX_DOCUMENTS": cls.max_documents(),
        }

        missing_vars = [name for name, value in required_vars.items() if not value]

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

        logger.info("Configuration validated successfully")

    @classmethod
    def get_llm_models(cls) -> list[str]:
        """Get list of configured LLM model names.

        Returns:
            List of model names in order of priority.
        """
        models = [cls.model_name()]

        if cls.second_model_name():
            models.append(cls.second_model_name())

        if cls.third_model_name():
            models.append(cls.third_model_name())

        # Limit to NUM_LLM_MODELS
        return models[:cls.num_llm_models()]
