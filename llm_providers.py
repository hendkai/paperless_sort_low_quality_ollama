"""
LLM Providers Module

This module provides an abstract base class for LLM providers and concrete implementations
for various LLM services (Ollama, GLM, Claude API, GPT API, etc.).
"""

from abc import ABC, abstractmethod
import logging
from typing import Optional


logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All LLM provider implementations must inherit from this class and implement
    the required methods for content evaluation and title generation.
    """

    def __init__(self, model: str, url: Optional[str] = None) -> None:
        """
        Initialize the LLM provider.

        Args:
            model: The model name/identifier to use
            url: Optional URL endpoint for the LLM service
        """
        self.model = model
        self.url = url
        self.logger = logger

    @abstractmethod
    def evaluate_content(self, content: str, prompt: str, document_id: int) -> str:
        """
        Evaluate document content and return quality assessment.

        Args:
            content: The document content to evaluate
            prompt: The prompt to use for evaluation
            document_id: The document ID for logging/tracking

        Returns:
            Quality assessment string (e.g., "low quality", "high quality")
        """
        pass

    @abstractmethod
    def generate_title(self, prompt: str, content: str) -> str:
        """
        Generate a title for the document content.

        Args:
            prompt: The prompt to use for title generation
            content: The document content to base the title on

        Returns:
            Generated title string
        """
        pass
