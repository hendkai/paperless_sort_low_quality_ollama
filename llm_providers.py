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


class GLMProvider(BaseLLMProvider):
    """
    GLM (Zhipu AI / z.ai) LLM provider implementation.

    This provider interfaces with Zhipu AI's GLM API to evaluate
    document content and generate titles.
    """

    def __init__(self, api_key: str, model: str, url: Optional[str] = None) -> None:
        """
        Initialize the GLM provider.

        Args:
            api_key: The API key for Zhipu AI
            model: The model name to use (e.g., glm-4, glm-3-turbo)
            url: Optional custom URL endpoint (defaults to https://open.bigmodel.cn/api/paas/v4/chat/completions)
        """
        super().__init__(model=model, url=url or "https://open.bigmodel.cn/api/paas/v4/chat/completions")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def evaluate_content(self, content: str, prompt: str, document_id: int) -> str:
        """
        Evaluate document content using GLM and return quality assessment.

        Args:
            content: The document content to evaluate
            prompt: The prompt to use for evaluation
            document_id: The document ID for logging/tracking

        Returns:
            Quality assessment string ("low quality", "high quality", or empty string on error)
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": f"{prompt}{content}"}
            ],
            "temperature": 0.3,
            "max_tokens": 100
        }

        try:
            response = requests.post(self.url, json=payload, headers=self.headers, timeout=60)
            response.raise_for_status()
            response_data = response.json()

            # Extract content from GLM response
            if 'choices' in response_data and len(response_data['choices']) > 0:
                full_response = response_data['choices'][0]['message']['content'].strip()

                # Check for quality assessment in response
                if "high quality" in full_response.lower():
                    return "high quality"
                elif "low quality" in full_response.lower():
                    return "low quality"
                else:
                    return ''
            else:
                self.logger.error(f"Unexpected response format from GLM for document ID {document_id}")
                return ''

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error sending request to GLM for document ID {document_id}: {e}")
            return ''
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            self.logger.error(f"Error parsing GLM response for document ID {document_id}: {e}")
            return ''

    def generate_title(self, prompt: str, content: str) -> str:
        """
        Generate a title for the document content using GLM.

        Args:
            prompt: The prompt to use for title generation
            content: The document content to base the title on

        Returns:
            Generated title string
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 50
        }

        try:
            response = requests.post(self.url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            response_data = response.json()

            # Extract title from GLM response
            if 'choices' in response_data and len(response_data['choices']) > 0:
                title = response_data['choices'][0]['message']['content'].strip()

                # Clean the response from quotes or other formatting
                title = title.replace('"', '').replace("'", '').replace('**', '')

                self.logger.info(f"GLM hat folgenden Titel generiert: '{title}'")
                return title
            else:
                self.logger.error("Unexpected response format from GLM for title generation")
                return ''

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error sending request to GLM for title generation: {e}")
            return ''
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            self.logger.error(f"Error parsing GLM response for title generation: {e}")
            return ''


class ClaudeAPIProvider(BaseLLMProvider):
    """
    Claude (Anthropic) API provider implementation.

    This provider interfaces with Anthropic's Claude API to evaluate
    document content and generate titles.
    """

    def __init__(self, api_key: str, model: str, url: Optional[str] = None) -> None:
        """
        Initialize the Claude API provider.

        Args:
            api_key: The API key for Anthropic
            model: The model name to use (e.g., claude-3-5-sonnet-20241022, claude-3-haiku-20240307)
            url: Optional custom URL endpoint (defaults to https://api.anthropic.com/v1/messages)
        """
        super().__init__(model=model, url=url or "https://api.anthropic.com/v1/messages")
        self.api_key = api_key
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

    def evaluate_content(self, content: str, prompt: str, document_id: int) -> str:
        """
        Evaluate document content using Claude and return quality assessment.

        Args:
            content: The document content to evaluate
            prompt: The prompt to use for evaluation
            document_id: The document ID for logging/tracking

        Returns:
            Quality assessment string ("low quality", "high quality", or empty string on error)
        """
        payload = {
            "model": self.model,
            "max_tokens": 100,
            "messages": [
                {"role": "user", "content": f"{prompt}{content}"}
            ],
            "temperature": 0.3
        }

        try:
            response = requests.post(self.url, json=payload, headers=self.headers, timeout=60)
            response.raise_for_status()
            response_data = response.json()

            # Extract content from Claude response
            if 'content' in response_data and len(response_data['content']) > 0:
                full_response = response_data['content'][0]['text'].strip()

                # Check for quality assessment in response
                if "high quality" in full_response.lower():
                    return "high quality"
                elif "low quality" in full_response.lower():
                    return "low quality"
                else:
                    return ''
            else:
                self.logger.error(f"Unexpected response format from Claude for document ID {document_id}")
                return ''

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error sending request to Claude for document ID {document_id}: {e}")
            return ''
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            self.logger.error(f"Error parsing Claude response for document ID {document_id}: {e}")
            return ''

    def generate_title(self, prompt: str, content: str) -> str:
        """
        Generate a title for the document content using Claude.

        Args:
            prompt: The prompt to use for title generation
            content: The document content to base the title on

        Returns:
            Generated title string
        """
        payload = {
            "model": self.model,
            "max_tokens": 50,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }

        try:
            response = requests.post(self.url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            response_data = response.json()

            # Extract title from Claude response
            if 'content' in response_data and len(response_data['content']) > 0:
                title = response_data['content'][0]['text'].strip()

                # Clean the response from quotes or other formatting
                title = title.replace('"', '').replace("'", '').replace('**', '')

                self.logger.info(f"Claude hat folgenden Titel generiert: '{title}'")
                return title
            else:
                self.logger.error("Unexpected response format from Claude for title generation")
                return ''

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error sending request to Claude for title generation: {e}")
            return ''
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            self.logger.error(f"Error parsing Claude response for title generation: {e}")
            return ''


class EnsembleLLMService:
    """
    Ensemble LLM service that combines multiple LLM providers for consensus-based evaluation.

    This service takes multiple LLM provider instances and evaluates content using all of them,
    then applies consensus logic to determine the final result.
    """

    def __init__(self, services: list) -> None:
        """
        Initialize the ensemble service with a list of LLM provider instances.

        Args:
            services: List of BaseLLMProvider instances to use for ensemble evaluation
        """
        self.services = services
        self.logger = logger

    def evaluate_content(self, content: str, prompt: str, document_id: int) -> tuple:
        """
        Evaluate content using all providers and return consensus result.

        Args:
            content: The document content to evaluate
            prompt: The prompt to use for evaluation
            document_id: The document ID for logging/tracking

        Returns:
            Tuple of (consensus_result, consensus_reached)
            - consensus_result: The agreed-upon quality assessment string
            - consensus_reached: Boolean indicating if consensus was achieved
        """
        results = []
        for service in self.services:
            result = service.evaluate_content(content, prompt, document_id)
            self.logger.info(f"Model {service.model} result for document ID {document_id}: {result}")
            if result:
                results.append(result)

        consensus_result, consensus_reached = self.consensus_logic(results)
        return consensus_result, consensus_reached

    def consensus_logic(self, results: list) -> tuple:
        """
        Apply consensus logic to determine the final result from multiple provider outputs.

        Args:
            results: List of results from multiple LLM providers

        Returns:
            Tuple of (consensus_result, consensus_reached)
            - consensus_result: The agreed-upon result (empty string if no consensus)
            - consensus_reached: Boolean indicating if consensus was achieved
        """
        if not results:
            return '', False

        result_count = {}
        for result in results:
            if result in result_count:
                result_count[result] += 1
            else:
                result_count[result] = 1

        max_count = max(result_count.values())
        majority_results = [result for result, count in result_count.items() if count == max_count]

        if len(majority_results) == 1:
            return majority_results[0], True
        else:
            return '', False
