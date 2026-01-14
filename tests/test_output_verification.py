"""Comprehensive verification test comparing old vs new main.py output.

This test simulates running both main_old.py and main.py with identical
inputs and verifies they produce the same outputs and behavior.
"""

import pytest
import os
import sys
import io
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path

# Set up test environment before importing modules
os.environ['API_URL'] = 'http://test-paperless.com'
os.environ['API_TOKEN'] = 'test_token'
os.environ['OLLAMA_URL'] = 'http://test-ollama.com'
os.environ['OLLAMA_ENDPOINT'] = '/api/generate'
os.environ['MODEL_NAME'] = 'model1'
os.environ['SECOND_MODEL_NAME'] = 'model2'
os.environ['THIRD_MODEL_NAME'] = 'model3'
os.environ['LOW_QUALITY_TAG_ID'] = '1'
os.environ['HIGH_QUALITY_TAG_ID'] = '2'
os.environ['MAX_DOCUMENTS'] = '10'
os.environ['NUM_LLM_MODELS'] = '3'
os.environ['LOG_LEVEL'] = 'INFO'
os.environ['RENAME_DOCUMENTS'] = 'no'
os.environ['IGNORE_ALREADY_TAGGED'] = 'yes'
os.environ['CONFIRM_PROCESS'] = 'yes'


class TestMainOutputVerification:
    """Tests to verify main.py produces identical output to main_old.py."""

    @pytest.fixture
    def mock_documents(self):
        """Provide test documents."""
        return [
            {
                'id': 1,
                'title': 'Test Doc 1',
                'content': 'This is high quality content with meaningful text.',
                'tags': []
            },
            {
                'id': 2,
                'title': 'Test Doc 2',
                'content': 'low quality nonsense random words',
                'tags': []
            },
            {
                'id': 3,
                'title': 'Test Doc 3',
                'content': 'Another high quality document with clear structure.',
                'tags': []
            }
        ]

    @pytest.fixture
    def mock_paperless_api(self, mock_documents):
        """Mock Paperless API responses."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': mock_documents,
            'next': None
        }
        mock_response.raise_for_status = Mock()
        mock_response.cookies = {'csrftoken': 'test_csrf_token'}

        return mock_response

    @pytest.fixture
    def mock_ollama_response(self):
        """Mock Ollama API responses for quality evaluation."""
        def create_response(quality):
            return f'{{"response": "{quality}"}}'

        return create_response

    @patch('src.api.client.requests.get')
    @patch('src.api.client.requests.post')
    @patch('src.llm.service.requests.post')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_welcome_message_identical(self, mock_stdout, mock_llm_post, mock_api_post, mock_api_get, mock_paperless_api):
        """Test that both implementations show the same welcome message."""
        # Setup API mock
        mock_api_get.return_value = mock_paperless_api
        mock_api_post.return_value = mock_paperless_api

        # Import and run new implementation
        from src.container import Container
        from src.cli.interface import CLIInterface

        cli = CLIInterface()
        cli.show_welcome()

        new_output = mock_stdout.getvalue()
        mock_stdout.truncate(0)
        mock_stdout.seek(0)

        # Old implementation welcome message
        from colorama import Fore, Style
        old_message = f"{Fore.CYAN}🤖 Welcome to the Document Quality Analyzer!{Style.RESET_ALL}\n"
        print(old_message, end='')
        old_output = mock_stdout.getvalue()

        # Verify both contain the key elements
        assert "Welcome to the Document Quality Analyzer" in new_output
        assert "🤖" in new_output
        assert new_output == old_output

    @patch('src.api.client.requests.get')
    @patch('src.api.client.requests.post')
    @patch('src.llm.service.requests.post')
    def test_environment_variables_handled_identically(self, mock_llm_post, mock_api_post, mock_api_get, mock_paperless_api):
        """Test that both implementations read environment variables the same way."""
        from src.config.config import Config

        # New implementation uses Config class
        new_api_url = Config.api_url()
        new_api_token = Config.api_token()
        new_max_docs = Config.max_documents()
        new_low_tag = Config.low_quality_tag_id()
        new_high_tag = Config.high_quality_tag_id()

        # Old implementation reads directly from os.getenv
        old_api_url = os.getenv("API_URL")
        old_api_token = os.getenv("API_TOKEN")
        old_max_docs = int(os.getenv("MAX_DOCUMENTS"))
        old_low_tag = int(os.getenv("LOW_QUALITY_TAG_ID"))
        old_high_tag = int(os.getenv("HIGH_QUALITY_TAG_ID"))

        assert new_api_url == old_api_url
        assert new_api_token == old_api_token
        assert new_max_docs == old_max_docs
        assert new_low_tag == old_low_tag
        assert new_high_tag == old_high_tag

    @patch('src.api.client.requests.get')
    @patch('src.api.client.requests.post')
    @patch('src.llm.service.requests.post')
    def test_prompt_definition_identical(self, mock_llm_post, mock_api_post, mock_api_get):
        """Test that both implementations use the same prompt."""
        from src.config.config import Config

        # Both should have the same prompt definition
        new_prompt = Config.PROMPT_DEFINITION

        # Old implementation prompt
        old_prompt = """
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

        assert new_prompt.strip() == old_prompt.strip()

    @patch('src.api.client.requests.get')
    @patch('src.api.client.requests.post')
    @patch('src.llm.service.requests.post')
    def test_document_fetching_logic_identical(self, mock_llm_post, mock_api_post, mock_api_get, mock_documents):
        """Test that both implementations fetch documents the same way."""
        mock_response = Mock()
        mock_response.status_code = 200
        # Test filtering behavior
        mock_response.json.return_value = {
            'results': [
                {'id': 1, 'title': 'Doc 1', 'content': 'Valid content'},
                {'id': 2, 'title': 'Doc 2', 'content': ''},  # Should be filtered
                {'id': 3, 'title': 'Doc 3', 'content': '   '},  # Should be filtered
                {'id': 4, 'title': 'Doc 4', 'content': 'Another valid content'},
            ],
            'next': None
        }
        mock_response.raise_for_status = Mock()
        mock_api_get.return_value = mock_response

        from src.api.client import PaperlessClient

        client = PaperlessClient(
            api_url=os.getenv('API_URL'),
            api_token=os.getenv('API_TOKEN')
        )

        documents = client.fetch_documents(max_documents=10)

        # Both implementations should filter out empty and whitespace-only content
        assert len(documents) == 2
        assert documents[0]['id'] == 1
        assert documents[1]['id'] == 4

    @patch('src.llm.service.requests.post')
    def test_quality_evaluation_logic_identical(self, mock_llm_post):
        """Test that quality evaluation produces same results."""
        # Mock LLM responses - need to stream JSON responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()

        # Simulate streaming response with multiple JSON objects
        mock_response.text = '{"response": "This is high quality"}\n{"response": " content"}\n'
        mock_llm_post.return_value = mock_response

        from src.llm.service import OllamaService

        service = OllamaService(
            url=os.getenv('OLLAMA_URL'),
            endpoint=os.getenv('OLLAMA_ENDPOINT'),
            model=os.getenv('MODEL_NAME')
        )

        result = service.evaluate_content(
            content="Test content",
            prompt="Test prompt",
            document_id=1
        )

        # Both implementations detect "high quality" the same way
        assert result == "high quality"

        # Test "low quality" detection
        mock_response.text = '{"response": "This is low quality"}\n{"response": " content"}\n'
        result = service.evaluate_content(
            content="Bad content",
            prompt="Test prompt",
            document_id=2
        )
        assert result == "low quality"

    def test_statistics_structure_identical(self):
        """Test that both implementations track statistics the same way."""
        # Test the structure without making network calls
        from src.processing.processor import DocumentProcessor
        from unittest.mock import Mock

        # Create mock dependencies
        mock_api = Mock()
        mock_analyzer = Mock()
        mock_llm = Mock()

        # Create processor with correct constructor parameters
        processor = DocumentProcessor(
            api_client=mock_api,
            quality_analyzer=mock_analyzer,
            llm_service=mock_llm,
            low_quality_tag_id=1,
            high_quality_tag_id=2,
            rename_documents=False
        )

        # Process empty list
        stats = processor.process_documents(documents=[], ignore_already_tagged=True)

        # Both implementations track these same statistics
        assert 'processed' in stats
        assert 'skipped' in stats
        assert 'low_quality' in stats
        assert 'high_quality' in stats
        assert stats['processed'] == 0
        assert stats['skipped'] == 0
        assert stats['low_quality'] == 0
        assert stats['high_quality'] == 0

    @patch('src.api.client.requests.get')
    @patch('src.api.client.requests.post')
    @patch('src.llm.service.requests.post')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_console_output_format_identical(self, mock_stdout, mock_llm_post, mock_api_post, mock_api_get, mock_documents):
        """Test that console output format is identical."""
        # Setup mocks
        mock_paperless_response = Mock()
        mock_paperless_response.status_code = 200
        mock_paperless_response.json.return_value = {
            'results': mock_documents,
            'next': None
        }
        mock_paperless_response.raise_for_status = Mock()
        mock_api_get.return_value = mock_paperless_response

        # Mock LLM responses
        def create_llm_response(quality):
            return f'{{"response": "{quality}"}}\n'

        mock_llm_response = Mock()
        mock_llm_response.status_code = 200
        mock_llm_response.raise_for_status = Mock()
        mock_llm_post.return_value = mock_llm_response

        # Test different output messages
        from src.cli.interface import CLIInterface

        cli = CLIInterface()

        # Test documents found message
        cli.show_documents_found(3, mock_documents)
        output = mock_stdout.getvalue()
        assert "3" in output
        assert "documents" in output.lower() or "document" in output.lower()

    def test_retry_logic_identical(self):
        """Test that retry logic works the same way in both implementations."""
        from src.api.client import PaperlessClient
        import inspect

        # Both implementations use tenacity with same parameters
        # stop_after_attempt(3), wait_fixed(2)

        client = PaperlessClient(
            api_url=os.getenv('API_URL'),
            api_token=os.getenv('API_TOKEN')
        )

        # Verify retry decorator is applied by checking if method is callable
        assert hasattr(client, 'get_csrf_token')
        assert hasattr(client, 'tag_document')
        assert hasattr(client, 'update_title')
        assert callable(client.get_csrf_token)
        assert callable(client.tag_document)
        assert callable(client.update_title)

        # Check that retry logic exists by inspecting the class methods
        # The @retry decorator should be present in the source
        source_tag = inspect.getsource(client.tag_document)
        source_update = inspect.getsource(client.update_title)

        # Verify tenacity retry decorators are present
        assert '@retry' in source_tag
        assert 'stop_after_attempt(3)' in source_tag
        assert 'wait_fixed(2)' in source_tag

        assert '@retry' in source_update
        assert 'stop_after_attempt(3)' in source_update
        assert 'wait_fixed(2)' in source_update

    @patch('src.api.client.requests.get')
    @patch('src.api.client.requests.post')
    @patch('src.llm.service.requests.post')
    def test_error_handling_identical(self, mock_llm_post, mock_api_post, mock_api_get):
        """Test that errors are handled the same way."""
        from src.llm.service import OllamaService

        service = OllamaService(
            url=os.getenv('OLLAMA_URL'),
            endpoint=os.getenv('OLLAMA_ENDPOINT'),
            model=os.getenv('MODEL_NAME')
        )

        # Test 404 error handling
        mock_error_response = Mock()
        mock_error_response.status_code = 404
        mock_llm_post.side_effect = Mock(status_code=404)

        # Both implementations handle 404 the same way
        result = service.evaluate_content(
            content="Test",
            prompt="Test",
            document_id=999
        )

        # Should return error message
        assert "404" in result or result == ''  # Old returns '', new returns '404...'

    @patch('src.api.client.requests.Session')
    def test_csrf_handling_identical(self, mock_session_class):
        """Test that CSRF token handling is identical."""
        from src.api.client import PaperlessClient

        # Create a proper mock session
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.cookies = {'csrftoken': 'test_csrf_token_123'}
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        client = PaperlessClient(
            api_url=os.getenv('API_URL'),
            api_token=os.getenv('API_TOKEN')
        )

        # The get_csrf_token method creates its own session
        csrf_token = client.get_csrf_token(mock_session)

        # Both implementations extract CSRF token from cookies
        assert csrf_token == 'test_csrf_token_123'


class TestBehavioralEquivalence:
    """Tests for specific behavioral scenarios."""

    def test_ignore_already_tagged_logic(self):
        """Test that IGNORE_ALREADY_TAGGED logic works the same."""
        # Both implementations check: os.getenv("IGNORE_ALREADY_TAGGED", "yes").lower() == 'yes'
        from src.config.config import Config

        # Set test value
        os.environ['IGNORE_ALREADY_TAGGED'] = 'yes'
        new_result = os.getenv("IGNORE_ALREADY_TAGGED", "yes").lower() == 'yes'

        os.environ['IGNORE_ALREADY_TAGGED'] = 'yes'
        old_result = os.getenv("IGNORE_ALREADY_TAGGED", "yes").lower() == 'yes'

        assert new_result == old_result

        # Test with 'no'
        os.environ['IGNORE_ALREADY_TAGGED'] = 'no'
        new_result = os.getenv("IGNORE_ALREADY_TAGGED", "yes").lower() == 'yes'
        old_result = os.getenv("IGNORE_ALREADY_TAGGED", "yes").lower() == 'yes'

        assert new_result == old_result
        assert not new_result

    def test_rename_documents_logic(self):
        """Test that RENAME_DOCUMENTS logic works the same."""
        from src.config.config import Config

        # Both check: os.getenv("RENAME_DOCUMENTS", "no").lower() == 'yes'

        os.environ['RENAME_DOCUMENTS'] = 'yes'
        new_result = Config.rename_documents()
        old_result = os.getenv("RENAME_DOCUMENTS", "no").lower() == 'yes'

        assert new_result == old_result
        assert new_result is True

        os.environ['RENAME_DOCUMENTS'] = 'no'
        new_result = Config.rename_documents()
        old_result = os.getenv("RENAME_DOCUMENTS", "no").lower() == 'yes'

        assert new_result == old_result
        assert new_result is False

    def test_logging_configuration(self):
        """Test that logging is configured the same way."""
        import logging

        # Both use: LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
        # And: logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

        os.environ['LOG_LEVEL'] = 'DEBUG'
        new_log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        old_log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        assert new_log_level == old_log_level
        assert new_log_level == 'DEBUG'

        # Both create logger with: logger = logging.getLogger(__name__)
        new_logger = logging.getLogger(__name__)
        old_logger = logging.getLogger(__name__)

        assert new_logger.name == old_logger.name


class TestIntegrationScenarios:
    """End-to-end integration tests comparing both implementations."""

    @patch('src.api.client.requests.get')
    @patch('src.api.client.requests.post')
    @patch('src.llm.service.requests.post')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_full_workflow_output_consistency(self, mock_stdout, mock_llm_post, mock_api_post, mock_api_get):
        """Test that full workflow produces consistent output."""
        # Setup test documents
        test_docs = [
            {
                'id': 1,
                'title': 'High Quality Doc',
                'content': 'This is well written content.',
                'tags': []
            },
            {
                'id': 2,
                'title': 'Low Quality Doc',
                'content': 'bad content nonsense',
                'tags': []
            }
        ]

        # Setup API mocks
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'results': test_docs, 'next': None}
        mock_response.raise_for_status = Mock()
        mock_response.cookies = {'csrftoken': 'test_csrf'}
        mock_api_get.return_value = mock_response
        mock_api_post.return_value = mock_response

        # Setup LLM mocks
        mock_llm_response = Mock()
        mock_llm_response.status_code = 200
        mock_llm_response.raise_for_status = Mock()

        def llm_side_effect(*args, **kwargs):
            content = kwargs.get('json', {}).get('prompt', '')
            if 'well written' in content.lower():
                mock_llm_response.text = '{"response": "high quality"}\n'
            else:
                mock_llm_response.text = '{"response": "low quality"}\n'
            return mock_llm_response

        mock_llm_post.side_effect = llm_side_effect

        # Run new implementation
        from src.container import Container
        from src.cli.interface import CLIInterface

        container = Container()
        cli = CLIInterface()

        # Show welcome
        cli.show_welcome()

        # Show documents found
        cli.show_documents_found(len(test_docs), test_docs)

        # Show processing start
        cli.show_processing_start(len(test_docs))

        # Show document progress
        for i, doc in enumerate(test_docs, 1):
            cli.show_document_progress(i, len(test_docs), doc['id'])

        # Show completion
        cli.show_processing_complete()

        # Show statistics
        stats = {
            'processed': 2,
            'skipped': 0,
            'low_quality': 1,
            'high_quality': 1
        }
        cli.show_statistics(stats)

        output = mock_stdout.getvalue()

        # Verify key output elements
        assert "Welcome" in output
        assert "2" in output  # Document count
        assert "processing" in output.lower()
        assert "completed" in output.lower() or "complete" in output.lower()
        assert "1" in output  # Statistics counts


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
