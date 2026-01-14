"""
LLM Providers Module

This module provides an abstract base class for LLM providers and concrete implementations
for various LLM services (Ollama, GLM, Claude API, GPT API, etc.).
"""

from abc import ABC, abstractmethod
import logging
from typing import Optional
import requests
import json


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


class OllamaService(BaseLLMProvider):
    """
    Ollama LLM provider implementation.

    This provider interfaces with Ollama's local LLM service to evaluate
    document content and generate titles.
    """

    def __init__(self, url: str, endpoint: str, model: str) -> None:
        """
        Initialize the Ollama service.

        Args:
            url: The base URL of the Ollama service
            endpoint: The API endpoint for Ollama (e.g., /api/generate)
            model: The model name to use for generation
        """
        super().__init__(model=model, url=url)
        self.endpoint = endpoint

    def evaluate_content(self, content: str, prompt: str, document_id: int) -> str:
        """
        Evaluate document content using Ollama and return quality assessment.

        Args:
            content: The document content to evaluate
            prompt: The prompt to use for evaluation
            document_id: The document ID for logging/tracking

        Returns:
            Quality assessment string ("low quality", "high quality", or empty string on error)
        """
        payload = {"model": self.model, "prompt": f"{prompt}{content}"}
        try:
            response = requests.post(f"{self.url}{self.endpoint}", json=payload)
            response.raise_for_status()
            responses = response.text.strip().split("\n")
            full_response = ""
            for res in responses:
                try:
                    res_json = json.loads(res)
                    if 'response' in res_json:
                        full_response += res_json['response']
                except json.JSONDecodeError as e:
                    self.logger.error(f"Error decoding JSON object for document ID {document_id}: {e}")
                    self.logger.error(f"Response text: {res}")
            if "high quality" in full_response.lower():
                return "high quality"
            elif "low quality" in full_response.lower():
                return "low quality"
            else:
                return ''
        except requests.exceptions.RequestException as e:
            if response.status_code == 404:
                self.logger.error(f"404 Client Error: Not Found for document ID {document_id}: {e}")
                return '404 Client Error: Not Found'
            else:
                self.logger.error(f"Error sending request to Ollama for document ID {document_id}: {e}")
                return ''

    def generate_title(self, prompt: str, content: str) -> str:
        """
        Generate a title for the document content using Ollama.

        Args:
            prompt: The prompt to use for title generation
            content: The document content to base the title on

        Returns:
            Generated title string
        """
        payload = {"model": self.model, "prompt": prompt}
        try:
            response = requests.post(f"{self.url}{self.endpoint}", json=payload)
            response.raise_for_status()
            responses = response.text.strip().split("\n")
            full_response = ""
            for res in responses:
                try:
                    res_json = json.loads(res)
                    if 'response' in res_json:
                        full_response += res_json['response']
                except json.JSONDecodeError as e:
                    self.logger.error(f"Error decoding JSON object for title generation: {e}")
                    self.logger.error(f"Response text: {res}")

            # Clean the response from quotes or other formatting
            title = full_response.strip().replace('"', '').replace("'", '')
            self.logger.info(f"LLM hat folgenden Titel generiert: '{title}'")
            return title
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error sending request to Ollama for title generation: {e}")
            return ''
