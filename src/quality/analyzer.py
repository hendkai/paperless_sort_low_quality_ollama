"""Quality analyzer module for evaluating document quality using LLM services."""

import logging
from typing import Tuple, Optional
from src.llm.service import EnsembleOllamaService


logger = logging.getLogger(__name__)


class QualityAnalyzer:
    """Analyzer for evaluating document quality using ensemble LLM services.

    This class coordinates quality evaluation by:
    1. Sending document content to LLM ensemble for evaluation
    2. Parsing and validating the quality response
    3. Determining the appropriate quality classification
    """

    def __init__(self, llm_service: EnsembleOllamaService, quality_prompt: str) -> None:
        """Initialize QualityAnalyzer.

        Args:
            llm_service: Ensemble LLM service for quality evaluation
            quality_prompt: Prompt template for quality evaluation
        """
        self.llm_service = llm_service
        self.quality_prompt = quality_prompt

    def evaluate(self, content: str, document_id: int) -> Tuple[str, bool]:
        """Evaluate document quality using LLM ensemble.

        Args:
            content: Document content to evaluate
            document_id: Document ID for logging

        Returns:
            Tuple of (quality_result, consensus_reached)
            - quality_result: "high quality", "low quality", or empty string if evaluation fails
            - consensus_reached: True if ensemble consensus was achieved, False otherwise
        """
        logger.info(f"Evaluating quality for document ID {document_id}")

        quality_response, consensus_reached = self.llm_service.evaluate_content(
            content, self.quality_prompt, document_id
        )

        logger.info(f"Quality evaluation for document ID {document_id}: {quality_response}")
        logger.info(f"Consensus reached: {consensus_reached}")

        # Validate and normalize the response
        validated_quality = self._validate_quality_response(quality_response)

        if validated_quality:
            logger.info(
                f"Document {document_id} evaluated as '{validated_quality}' "
                f"(consensus: {consensus_reached})"
            )
        else:
            logger.warning(
                f"Could not determine quality for document {document_id}. "
                f"Raw response: '{quality_response}'"
            )

        return validated_quality, consensus_reached

    def _validate_quality_response(self, response: str) -> str:
        """Validate and normalize quality evaluation response.

        Args:
            response: Raw response from LLM service

        Returns:
            Normalized "high quality" or "low quality", or empty string if invalid
        """
        if not response:
            return ''

        response_lower = response.lower().strip()

        if response_lower == 'high quality':
            return 'high quality'
        elif response_lower == 'low quality':
            return 'low quality'
        elif 'high quality' in response_lower:
            return 'high quality'
        elif 'low quality' in response_lower:
            return 'low quality'
        else:
            return ''

    def determine_tag_action(self, quality_result: str, consensus_reached: bool) -> Tuple[Optional[str], bool]:
        """Determine what action should be taken based on quality evaluation.

        Args:
            quality_result: Quality evaluation result ("high quality", "low quality", or empty)
            consensus_reached: Whether ensemble consensus was achieved

        Returns:
            Tuple of (action, should_process)
            - action: "tag_low", "tag_high", or "skip"
            - should_process: True if document should be processed, False if it should be skipped
        """
        if not consensus_reached:
            logger.info("No consensus reached - document will be skipped")
            return "skip", False

        if quality_result == 'low quality':
            return "tag_low", True
        elif quality_result == 'high quality':
            return "tag_high", True
        else:
            logger.info(f"Invalid quality result '{quality_result}' - document will be skipped")
            return "skip", False

    def is_high_quality(self, quality_result: str) -> bool:
        """Check if quality result indicates high quality.

        Args:
            quality_result: Quality evaluation result

        Returns:
            True if quality is high, False otherwise
        """
        return quality_result == 'high quality'

    def is_low_quality(self, quality_result: str) -> bool:
        """Check if quality result indicates low quality.

        Args:
            quality_result: Quality evaluation result

        Returns:
            True if quality is low, False otherwise
        """
        return quality_result == 'low quality'
