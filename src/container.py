"""Dependency injection container for managing application components.

This container creates and wires together all application modules following
dependency injection principles for testability and maintainability.
"""

import logging
from typing import Optional

from src.config.config import Config
from src.api.client import PaperlessClient
from src.llm.service import OllamaService, EnsembleOllamaService
from src.quality.analyzer import QualityAnalyzer
from src.processing.processor import DocumentProcessor
from src.cli.interface import CLIInterface


logger = logging.getLogger(__name__)


class Container:
    """Dependency injection container for application components.

    This container manages the creation and lifecycle of all application
    services, ensuring proper dependency injection and enabling easy testing.
    """

    def __init__(self, validate_config: bool = True) -> None:
        """Initialize the container.

        Args:
            validate_config: If True, validate configuration on initialization.
        """
        logger.info("Initializing Container")

        # Validate configuration if requested
        if validate_config:
            Config.validate()

        # Lazy-initialized components (cached as private attributes)
        self._config: Optional[Config] = None
        self._api_client: Optional[PaperlessClient] = None
        self._llm_service: Optional[OllamaService] = None
        self._ensemble_llm_service: Optional[EnsembleOllamaService] = None
        self._quality_analyzer: Optional[QualityAnalyzer] = None
        self._document_processor: Optional[DocumentProcessor] = None
        self._cli_interface: Optional[CLIInterface] = None

        logger.info("Container initialized successfully")

    @property
    def config(self) -> Config:
        """Get configuration singleton.

        Returns:
            Config instance for accessing environment variables.
        """
        if self._config is None:
            self._config = Config()
            logger.debug("Config instance created")
        return self._config

    @property
    def api_client(self) -> PaperlessClient:
        """Get Paperless API client singleton.

        Returns:
            Configured PaperlessClient instance.
        """
        if self._api_client is None:
            self._api_client = PaperlessClient(
                api_url=self.config.api_url(),
                api_token=self.config.api_token()
            )
            logger.debug("PaperlessClient instance created")
        return self._api_client

    @property
    def llm_service(self) -> OllamaService:
        """Get primary LLM service singleton for title generation.

        Returns:
            Configured OllamaService instance using primary model.
        """
        if self._llm_service is None:
            self._llm_service = OllamaService(
                url=self.config.ollama_url(),
                endpoint=self.config.ollama_endpoint(),
                model=self.config.model_name()
            )
            logger.debug(f"OllamaService instance created with model: {self.config.model_name()}")
        return self._llm_service

    @property
    def ensemble_llm_service(self) -> EnsembleOllamaService:
        """Get ensemble LLM service singleton for quality evaluation.

        Returns:
            Configured EnsembleOllamaService with multiple models.
        """
        if self._ensemble_llm_service is None:
            # Create individual services for each configured model
            model_names = self.config.get_llm_models()
            services = [
                OllamaService(
                    url=self.config.ollama_url(),
                    endpoint=self.config.ollama_endpoint(),
                    model=model_name
                )
                for model_name in model_names
            ]
            self._ensemble_llm_service = EnsembleOllamaService(services)
            logger.debug(f"EnsembleOllamaService instance created with {len(services)} models")
        return self._ensemble_llm_service

    @property
    def quality_analyzer(self) -> QualityAnalyzer:
        """Get quality analyzer singleton.

        Returns:
            Configured QualityAnalyzer instance.
        """
        if self._quality_analyzer is None:
            self._quality_analyzer = QualityAnalyzer(
                llm_service=self.ensemble_llm_service,
                quality_prompt=self.config.PROMPT_DEFINITION
            )
            logger.debug("QualityAnalyzer instance created")
        return self._quality_analyzer

    @property
    def document_processor(self) -> DocumentProcessor:
        """Get document processor singleton.

        Returns:
            Configured DocumentProcessor instance with all dependencies.
        """
        if self._document_processor is None:
            self._document_processor = DocumentProcessor(
                api_client=self.api_client,
                quality_analyzer=self.quality_analyzer,
                llm_service=self.llm_service,
                low_quality_tag_id=self.config.low_quality_tag_id(),
                high_quality_tag_id=self.config.high_quality_tag_id(),
                rename_documents=self.config.rename_documents()
            )
            logger.debug("DocumentProcessor instance created")
        return self._document_processor

    @property
    def cli_interface(self) -> CLIInterface:
        """Get CLI interface singleton.

        Returns:
            Configured CLIInterface instance.
        """
        if self._cli_interface is None:
            self._cli_interface = CLIInterface()
            logger.debug("CLIInterface instance created")
        return self._cli_interface

    def reset(self) -> None:
        """Reset all cached instances.

        This method clears all singleton instances, forcing them to be
        recreated on next access. Useful for testing or reconfiguration.
        """
        logger.info("Resetting container instances")
        self._config = None
        self._api_client = None
        self._llm_service = None
        self._ensemble_llm_service = None
        self._quality_analyzer = None
        self._document_processor = None
        self._cli_interface = None
        logger.debug("All container instances reset")
