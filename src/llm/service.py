import requests
import json
import logging
from typing import List, Tuple


logger = logging.getLogger(__name__)


class OllamaService:
    """Service for interacting with a single Ollama LLM model."""

    def __init__(self, url: str, endpoint: str, model: str) -> None:
        """
        Initialize OllamaService.

        Args:
            url: Base URL for the Ollama API
            endpoint: API endpoint path
            model: Model name to use
        """
        self.url = url
        self.endpoint = endpoint
        self.model = model

    def evaluate_content(self, content: str, prompt: str, document_id: int) -> str:
        """
        Evaluate content quality using the LLM.

        Args:
            content: Document content to evaluate
            prompt: Prompt template to use
            document_id: Document ID for logging

        Returns:
            "high quality", "low quality", or empty string on error
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
                    logger.error(f"Error decoding JSON object for document ID {document_id}: {e}")
                    logger.error(f"Response text: {res}")
            if "high quality" in full_response.lower():
                return "high quality"
            elif "low quality" in full_response.lower():
                return "low quality"
            else:
                return ''
        except requests.exceptions.RequestException as e:
            if response.status_code == 404:
                logger.error(f"404 Client Error: Not Found for document ID {document_id}: {e}")
                return '404 Client Error: Not Found'
            else:
                logger.error(f"Error sending request to Ollama for document ID {document_id}: {e}")
                return ''

    def generate_title(self, prompt: str, content_for_id: str) -> str:
        """
        Generate a title for document content.

        Args:
            prompt: Prompt template for title generation
            content_for_id: Document content (not currently used in prompt)

        Returns:
            Generated title or empty string on error
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
                    logger.error(f"Error decoding JSON object for title generation: {e}")
                    logger.error(f"Response text: {res}")

            # Clean up response from quotes or other formatting
            title = full_response.strip().replace('"', '').replace("'", '')
            logger.info(f"LLM generated title: '{title}'")
            return title
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending request to Ollama for title generation: {e}")
            return ''


class EnsembleOllamaService:
    """Service for ensemble evaluation using multiple Ollama models."""

    def __init__(self, services: List[OllamaService]) -> None:
        """
        Initialize EnsembleOllamaService.

        Args:
            services: List of OllamaService instances for ensemble
        """
        self.services = services

    def evaluate_content(self, content: str, prompt: str, document_id: int) -> Tuple[str, bool]:
        """
        Evaluate content using ensemble of multiple models.

        Args:
            content: Document content to evaluate
            prompt: Prompt template to use
            document_id: Document ID for logging

        Returns:
            Tuple of (consensus_result, consensus_reached)
            - consensus_result: "high quality", "low quality", or empty string
            - consensus_reached: True if consensus was achieved, False otherwise
        """
        results = []
        for service in self.services:
            result = service.evaluate_content(content, prompt, document_id)
            logger.info(f"Model {service.model} result for document ID {document_id}: {result}")
            if result:
                results.append(result)

        consensus_result, consensus_reached = self.consensus_logic(results)
        return consensus_result, consensus_reached

    def consensus_logic(self, results: List[str]) -> Tuple[str, bool]:
        """
        Determine consensus from multiple model results.

        Args:
            results: List of evaluation results from multiple models

        Returns:
            Tuple of (consensus_result, consensus_reached)
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
