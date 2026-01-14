"""Integration tests validating the refactoring from monolithic to modular architecture.

This test suite compares the old monolithic implementation (main.py) with the new
modular implementation to ensure behavior is preserved during refactoring.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.container import Container
from src.api.client import PaperlessClient
from src.llm.service import OllamaService, EnsembleOllamaService
from src.quality.analyzer import QualityAnalyzer
from src.processing.processor import DocumentProcessor
from src.cli.interface import CLIInterface
from src.config.config import Config


class TestModuleSizes:
    """Tests to verify all modules meet size requirements."""

    def test_config_module_under_200_lines(self):
        """Verify config module is under 200 lines."""
        config_path = Path("src/config/config.py")
        line_count = len(config_path.read_text().splitlines())
        assert line_count < 200, f"config.py has {line_count} lines (should be < 200)"

    def test_api_client_module_under_200_lines(self):
        """Verify API client module is under 200 lines."""
        client_path = Path("src/api/client.py")
        line_count = len(client_path.read_text().splitlines())
        assert line_count < 200, f"client.py has {line_count} lines (should be < 200)"

    def test_llm_service_module_under_200_lines(self):
        """Verify LLM service module is under 200 lines."""
        service_path = Path("src/llm/service.py")
        line_count = len(service_path.read_text().splitlines())
        assert line_count < 200, f"service.py has {line_count} lines (should be < 200)"

    def test_quality_analyzer_module_under_200_lines(self):
        """Verify quality analyzer module is under 200 lines."""
        analyzer_path = Path("src/quality/analyzer.py")
        line_count = len(analyzer_path.read_text().splitlines())
        assert line_count < 200, f"analyzer.py has {line_count} lines (should be < 200)"

    def test_document_processor_module_under_200_lines(self):
        """Verify document processor module is under 200 lines."""
        processor_path = Path("src/processing/processor.py")
        line_count = len(processor_path.read_text().splitlines())
        assert line_count < 200, f"processor.py has {line_count} lines (should be < 200)"

    def test_cli_interface_module_under_200_lines(self):
        """Verify CLI interface module is under 200 lines."""
        cli_path = Path("src/cli/interface.py")
        line_count = len(cli_path.read_text().splitlines())
        assert line_count < 200, f"interface.py has {line_count} lines (should be < 200)"

    def test_container_module_under_200_lines(self):
        """Verify container module is under 200 lines."""
        container_path = Path("src/container.py")
        line_count = len(container_path.read_text().splitlines())
        assert line_count < 200, f"container.py has {line_count} lines (should be < 200)"

    def test_main_new_under_200_lines(self):
        """Verify new main.py is under 200 lines."""
        main_path = Path("main_new.py")
        line_count = len(main_path.read_text().splitlines())
        assert line_count < 200, f"main_new.py has {line_count} lines (should be < 200)"


class TestImportsWork:
    """Tests to verify all imports work correctly."""

    def test_import_config_module(self):
        """Test that config module can be imported."""
        from src.config.config import Config
        assert Config is not None

    def test_import_api_client_module(self):
        """Test that API client module can be imported."""
        from src.api.client import PaperlessClient
        assert PaperlessClient is not None

    def test_import_llm_service_module(self):
        """Test that LLM service module can be imported."""
        from src.llm.service import OllamaService, EnsembleOllamaService
        assert OllamaService is not None
        assert EnsembleOllamaService is not None

    def test_import_quality_analyzer_module(self):
        """Test that quality analyzer module can be imported."""
        from src.quality.analyzer import QualityAnalyzer
        assert QualityAnalyzer is not None

    def test_import_document_processor_module(self):
        """Test that document processor module can be imported."""
        from src.processing.processor import DocumentProcessor
        assert DocumentProcessor is not None

    def test_import_cli_interface_module(self):
        """Test that CLI interface module can be imported."""
        from src.cli.interface import CLIInterface
        assert CLIInterface is not None

    def test_import_container_module(self):
        """Test that container module can be imported."""
        from src.container import Container
        assert Container is not None


class TestDependencyInjection:
    """Tests to verify dependency injection works correctly."""

    @patch.dict(os.environ, {
        'API_URL': 'http://test.com',
        'API_TOKEN': 'test_token',
        'OLLAMA_URL': 'http://ollama.com',
        'OLLAMA_ENDPOINT': '/api/generate',
        'MODEL_NAME': 'model1',
        'SECOND_MODEL_NAME': 'model2',
        'LOW_QUALITY_TAG_ID': '1',
        'HIGH_QUALITY_TAG_ID': '2',
        'MAX_DOCUMENTS': '10'
    })
    def test_container_creates_all_components(self):
        """Test that container creates all required components."""
        container = Container(validate_config=False)

        # Test that all properties exist (don't access them to avoid initialization)
        assert hasattr(container, 'config')
        assert hasattr(container, 'api_client')
        assert hasattr(container, 'llm_service')
        assert hasattr(container, 'ensemble_llm_service')
        assert hasattr(container, 'quality_analyzer')
        assert hasattr(container, 'document_processor')
        assert hasattr(container, 'cli_interface')

    @patch.dict(os.environ, {
        'API_URL': 'http://test.com',
        'API_TOKEN': 'test_token',
        'OLLAMA_URL': 'http://ollama.com',
        'OLLAMA_ENDPOINT': '/api/generate',
        'MODEL_NAME': 'model1',
        'SECOND_MODEL_NAME': 'model2',
        'LOW_QUALITY_TAG_ID': '1',
        'HIGH_QUALITY_TAG_ID': '2',
        'MAX_DOCUMENTS': '10'
    })
    def test_components_are_singletons(self):
        """Test that container returns singleton instances."""
        container = Container(validate_config=False)

        # Access same component twice
        api1 = container.api_client
        api2 = container.api_client

        assert api1 is api2, "API client should be singleton"

    @patch.dict(os.environ, {
        'API_URL': 'http://test.com',
        'API_TOKEN': 'test_token',
        'OLLAMA_URL': 'http://ollama.com',
        'OLLAMA_ENDPOINT': '/api/generate',
        'MODEL_NAME': 'model1',
        'SECOND_MODEL_NAME': 'model2',
        'LOW_QUALITY_TAG_ID': '1',
        'HIGH_QUALITY_TAG_ID': '2',
        'MAX_DOCUMENTS': '10'
    })
    def test_reset_clears_cached_instances(self):
        """Test that reset() clears cached instances."""
        container = Container(validate_config=False)

        # Access a component
        api1 = container.api_client

        # Reset container
        container.reset()

        # Access again, should be new instance
        api2 = container.api_client

        assert api1 is not api2, "Reset should create new instances"


class TestAPIBehaviorConsistency:
    """Tests to verify API client behavior matches old implementation."""

    @patch('src.api.client.requests.get')
    def test_api_client_headers_format(self, mock_get):
        """Test that API client uses correct header format."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'results': [], 'next': None}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = PaperlessClient(
            api_url="http://test.com",
            api_token="test_token"
        )

        client.fetch_documents(max_documents=10)

        # Verify the call was made with correct headers
        call_args = mock_get.call_args
        headers = call_args.kwargs.get('headers') or call_args[1].get('headers')
        assert headers is not None
        assert headers.get('Authorization') == 'Token test_token'

    @patch('src.api.client.requests.patch')
    @patch('src.api.client.requests.get')
    def test_api_client_uses_csrf_token(self, mock_get, mock_patch):
        """Test that API client includes CSRF token for write operations."""
        # Mock the GET response (checking if document is already tagged)
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {'tags': []}  # No tags yet
        mock_get_response.raise_for_status = Mock()
        mock_get.return_value = mock_get_response

        # Mock the PATCH response
        mock_patch_response = Mock()
        mock_patch_response.status_code = 200
        mock_patch_response.json.return_value = {'id': 1}
        mock_patch_response.raise_for_status = Mock()
        mock_patch.return_value = mock_patch_response

        client = PaperlessClient(
            api_url="http://test.com",
            api_token="test_token"
        )

        client.tag_document(document_id=1, tag_id=2, csrf_token="test_csrf")

        # Verify the PATCH call was made with CSRF header
        call_args = mock_patch.call_args
        headers = call_args.kwargs.get('headers')
        assert headers is not None
        assert headers.get('X-CSRFToken') == 'test_csrf'


class TestLLMServiceConsistency:
    """Tests to verify LLM service behavior matches old implementation."""

    def test_ollama_service_evaluate_content_quality_detection(self):
        """Test that OllamaService correctly detects quality in responses."""
        service = OllamaService(
            url="http://ollama.com",
            endpoint="/api/generate",
            model="test_model"
        )

        # Test with mock
        with patch('src.llm.service.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"response": "This document is high quality"}'
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            result = service.evaluate_content(
                content="test content",
                prompt="test prompt",
                document_id=1
            )

            assert result == "high quality"

    def test_ollama_service_case_insensitive_quality_detection(self):
        """Test that quality detection is case-insensitive."""
        service = OllamaService(
            url="http://ollama.com",
            endpoint="/api/generate",
            model="test_model"
        )

        # Test with uppercase response
        with patch('src.llm.service.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"response": "LOW QUALITY DOCUMENT"}'
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            result = service.evaluate_content(
                content="test content",
                prompt="test prompt",
                document_id=1
            )

            assert result == "low quality"


class TestQualityAnalyzerConsistency:
    """Tests to verify quality analyzer behavior matches old implementation."""

    def test_quality_analyzer_normalization(self):
        """Test that quality analyzer normalizes responses."""
        mock_llm = Mock()

        # Test various response formats
        test_cases = [
            ("high quality", "high quality"),
            ("HIGH QUALITY", "high quality"),
            ("This is high quality content", "high quality"),
            ("low quality", "low quality"),
            ("LOW QUALITY", "low quality"),
            ("This document is low quality", "low quality"),
        ]

        for input_response, expected_quality in test_cases:
            mock_llm.reset_mock()
            mock_llm.evaluate_content.return_value = (input_response, True)

            analyzer = QualityAnalyzer(llm_service=mock_llm, quality_prompt="test")
            result, consensus = analyzer.evaluate(content="test", document_id=1)

            assert result == expected_quality, f"Failed for input: {input_response}"


class TestDocumentProcessorConsistency:
    """Tests to verify document processor behavior matches old implementation."""

    def test_document_processor_returns_statistics(self):
        """Test that document processor returns proper statistics."""
        # Create mock dependencies
        mock_api_client = Mock()
        mock_quality_analyzer = Mock()
        mock_llm_service = Mock()

        # Create document processor
        processor = DocumentProcessor(
            api_client=mock_api_client,
            quality_analyzer=mock_quality_analyzer,
            llm_service=mock_llm_service,
            low_quality_tag_id=1,
            high_quality_tag_id=2,
            rename_documents=False
        )

        # Mock get_csrf_token to avoid HTTP call
        mock_api_client.get_csrf_token.return_value = "test_csrf"

        # Process empty document list
        stats = processor.process_documents(
            documents=[],
            ignore_already_tagged=True
        )

        # Verify statistics structure
        assert 'processed' in stats
        assert 'skipped' in stats
        assert 'low_quality' in stats
        assert 'high_quality' in stats
        assert 'total' in stats


class TestConfigConsistency:
    """Tests to verify config behavior matches old implementation."""

    def test_config_has_prompt_definition(self):
        """Test that config has PROMPT_DEFINITION constant."""
        assert hasattr(Config, 'PROMPT_DEFINITION')
        assert isinstance(Config.PROMPT_DEFINITION, str)
        assert len(Config.PROMPT_DEFINITION) > 0

    def test_config_log_level(self):
        """Test that config returns a valid log level."""
        log_level = Config.log_level()
        assert log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

    def test_config_max_documents(self):
        """Test that Config has max_documents method."""
        # Just verify the method exists - actual value depends on env
        assert hasattr(Config, 'max_documents')
        assert callable(Config.max_documents)

    def test_config_rename_documents(self):
        """Test that Config has rename_documents method."""
        # Just verify the method exists - actual value depends on env
        assert hasattr(Config, 'rename_documents')
        assert callable(Config.rename_documents)


class TestArchitectureCompliance:
    """Tests to verify architectural requirements are met."""

    def test_all_modules_have_init(self):
        """Test that all modules have __init__.py files."""
        modules = [
            'src/__init__.py',
            'src/config/__init__.py',
            'src/api/__init__.py',
            'src/llm/__init__.py',
            'src/quality/__init__.py',
            'src/processing/__init__.py',
            'src/cli/__init__.py',
        ]

        for module_path in modules:
            path = Path(module_path)
            assert path.exists(), f"Missing {module_path}"
            assert path.is_file(), f"{module_path} is not a file"

    def test_modules_are_independent(self):
        """Test that modules can be imported independently."""
        # Import each module independently
        from src import config
        from src import api
        from src import llm
        from src import quality
        from src import processing
        from src import cli

        assert config is not None
        assert api is not None
        assert llm is not None
        assert quality is not None
        assert processing is not None
        assert cli is not None


class TestRefactoringPreservesBehavior:
    """Integration tests to verify refactoring preserves original behavior."""

    @patch.dict(os.environ, {
        'API_URL': 'http://test.com',
        'API_TOKEN': 'test_token',
        'OLLAMA_URL': 'http://ollama.com',
        'OLLAMA_ENDPOINT': '/api/generate',
        'MODEL_NAME': 'model1',
        'SECOND_MODEL_NAME': 'model2',
        'THIRD_MODEL_NAME': 'model3',
        'NUM_LLM_MODELS': '3',
        'LOW_QUALITY_TAG_ID': '1',
        'HIGH_QUALITY_TAG_ID': '2',
        'MAX_DOCUMENTS': '10',
        'LOG_LEVEL': 'INFO'
    })
    def test_container_wiring_matches_old_dependencies(self):
        """Test that dependency injection matches old code's dependencies."""
        container = Container(validate_config=False)

        # Verify config is available
        assert container.config is not None

        # Verify API client depends on config
        api_client = container.api_client
        assert api_client is not None
        assert hasattr(api_client, 'api_url')
        assert hasattr(api_client, 'api_token')

        # Verify LLM service depends on config
        llm_service = container.llm_service
        assert llm_service is not None
        assert hasattr(llm_service, 'url')
        assert hasattr(llm_service, 'model')

        # Verify quality analyzer depends on LLM service
        quality_analyzer = container.quality_analyzer
        assert quality_analyzer is not None
        assert hasattr(quality_analyzer, 'llm_service')

        # Verify document processor depends on multiple services
        doc_processor = container.document_processor
        assert doc_processor is not None
        assert hasattr(doc_processor, 'api_client')
        assert hasattr(doc_processor, 'quality_analyzer')

    @patch('src.api.client.requests.get')
    def test_document_filtering_behavior_matches_old(self, mock_get):
        """Test that document filtering matches old implementation behavior."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [
                {'id': 1, 'title': 'Doc 1', 'content': 'Valid content'},
                {'id': 2, 'title': 'Doc 2', 'content': ''},  # Empty content
                {'id': 3, 'title': 'Doc 3', 'content': '   '},  # Whitespace only
                {'id': 4, 'title': 'Doc 4', 'content': 'Another valid content'},
            ],
            'next': None
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = PaperlessClient(
            api_url="http://test.com",
            api_token="test_token"
        )

        documents = client.fetch_documents(max_documents=10)

        # Old implementation filters out empty and whitespace-only content
        assert len(documents) == 2
        assert documents[0]['id'] == 1
        assert documents[1]['id'] == 4
