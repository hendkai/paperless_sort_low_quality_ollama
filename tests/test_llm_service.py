"""Unit tests for LLM service module."""

import pytest
from unittest.mock import Mock, patch
import requests
import json

from src.llm.service import OllamaService, EnsembleOllamaService


class TestOllamaServiceInit:
    """Tests for OllamaService initialization."""

    def test_init(self):
        """Test service initialization with correct parameters."""
        service = OllamaService(
            url="http://localhost:11434",
            endpoint="/api/generate",
            model="llama2"
        )
        assert service.url == "http://localhost:11434"
        assert service.endpoint == "/api/generate"
        assert service.model == "llama2"

    def test_init_with_different_params(self):
        """Test service initialization with different parameters."""
        service = OllamaService(
            url="https://ollama.example.com",
            endpoint="/v1/generate",
            model="mistral"
        )
        assert service.url == "https://ollama.example.com"
        assert service.endpoint == "/v1/generate"
        assert service.model == "mistral"


class TestOllamaServiceEvaluateContent:
    """Tests for OllamaService.evaluate_content method."""

    @patch('src.llm.service.requests.post')
    def test_evaluate_content_high_quality(self, mock_post):
        """Test successful evaluation returning 'high quality'."""
        mock_response = Mock()
        mock_response.status_code = 200
        # Simulate multi-line JSON response from Ollama
        mock_response.text = '''{"response": "This document is"}
{"response": " high quality"}
{"response": " material."}'''
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        service = OllamaService(
            url="http://localhost:11434",
            endpoint="/api/generate",
            model="llama2"
        )

        result = service.evaluate_content(
            content="Test content",
            prompt="Evaluate this: ",
            document_id=123
        )

        assert result == "high quality"
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "model" in call_args[1]['json']
        assert call_args[1]['json']['model'] == "llama2"

    @patch('src.llm.service.requests.post')
    def test_evaluate_content_low_quality(self, mock_post):
        """Test successful evaluation returning 'low quality'."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''{"response": "This is "}
{"response": "low quality"}'''
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        service = OllamaService(
            url="http://localhost:11434",
            endpoint="/api/generate",
            model="llama2"
        )

        result = service.evaluate_content(
            content="Test content",
            prompt="Evaluate: ",
            document_id=456
        )

        assert result == "low quality"

    @patch('src.llm.service.requests.post')
    def test_evaluate_content_no_match(self, mock_post):
        """Test evaluation when response doesn't match quality indicators."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''{"response": "The document is about finance"}
{"response": " and contains numbers."}'''
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        service = OllamaService(
            url="http://localhost:11434",
            endpoint="/api/generate",
            model="llama2"
        )

        result = service.evaluate_content(
            content="Test content",
            prompt="Evaluate: ",
            document_id=789
        )

        # Should return empty string when no match found
        assert result == ''

    @patch('src.llm.service.requests.post')
    def test_evaluate_content_case_insensitive(self, mock_post):
        """Test that quality detection is case-insensitive."""
        mock_response = Mock()
        mock_response.status_code = 200
        # Test with mixed case
        mock_response.text = '''{"response": "This is HIGH Quality"}'''
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        service = OllamaService(
            url="http://localhost:11434",
            endpoint="/api/generate",
            model="llama2"
        )

        result = service.evaluate_content(
            content="Test content",
            prompt="Evaluate: ",
            document_id=100
        )

        assert result == "high quality"

    @patch('src.llm.service.requests.post')
    def test_evaluate_content_with_invalid_json(self, mock_post):
        """Test evaluation when some JSON lines are invalid."""
        mock_response = Mock()
        mock_response.status_code = 200
        # Mix of valid and invalid JSON
        mock_response.text = '''{"response": "This is"}
invalid json line
{"response": " high quality"}'''
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        service = OllamaService(
            url="http://localhost:11434",
            endpoint="/api/generate",
            model="llama2"
        )

        result = service.evaluate_content(
            content="Test content",
            prompt="Evaluate: ",
            document_id=200
        )

        # Should still parse valid JSON and return result
        assert result == "high quality"

    @patch('src.llm.service.requests.post')
    def test_evaluate_content_404_error(self, mock_post):
        """Test evaluation when API returns 404 error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        # Create an exception with a response attribute
        exception = requests.exceptions.RequestException("404 Not Found")
        exception.response = mock_response

        mock_response.raise_for_status.side_effect = exception
        mock_post.return_value = mock_response

        service = OllamaService(
            url="http://localhost:11434",
            endpoint="/api/generate",
            model="llama2"
        )

        result = service.evaluate_content(
            content="Test content",
            prompt="Evaluate: ",
            document_id=300
        )

        # Should return specific 404 error message
        assert result == '404 Client Error: Not Found'

    @patch('src.llm.service.requests.post')
    def test_evaluate_content_request_exception(self, mock_post):
        """Test evaluation when request fails with general exception."""
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")

        service = OllamaService(
            url="http://localhost:11434",
            endpoint="/api/generate",
            model="llama2"
        )

        result = service.evaluate_content(
            content="Test content",
            prompt="Evaluate: ",
            document_id=400
        )

        # Should return empty string on error
        assert result == ''

    @patch('src.llm.service.requests.post')
    def test_evaluate_content_payload_construction(self, mock_post):
        """Test that payload is constructed correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"response": "high quality"}'
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        service = OllamaService(
            url="http://localhost:11434",
            endpoint="/api/generate",
            model="test-model"
        )

        service.evaluate_content(
            content="Document content here",
            prompt="Evaluate this document: ",
            document_id=1
        )

        # Verify payload construction
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['model'] == "test-model"
        assert payload['prompt'] == "Evaluate this document: Document content here"

    @patch('src.llm.service.requests.post')
    def test_evaluate_content_url_construction(self, mock_post):
        """Test that API URL is constructed correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"response": "high quality"}'
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        service = OllamaService(
            url="http://localhost:11434",
            endpoint="/api/generate",
            model="llama2"
        )

        service.evaluate_content(
            content="Test",
            prompt="Prompt: ",
            document_id=1
        )

        # Verify URL construction
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:11434/api/generate"


class TestOllamaServiceGenerateTitle:
    """Tests for OllamaService.generate_title method."""

    @patch('src.llm.service.requests.post')
    def test_generate_title_success(self, mock_post):
        """Test successful title generation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''{"response": "Invoice"}
{"response": " 2024-001"}'''
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        service = OllamaService(
            url="http://localhost:11434",
            endpoint="/api/generate",
            model="llama2"
        )

        title = service.generate_title(
            prompt="Generate a title for: Invoice #123",
            content_for_id="Some content"
        )

        assert title == "Invoice 2024-001"
        mock_post.assert_called_once()

    @patch('src.llm.service.requests.post')
    def test_generate_title_cleans_quotes(self, mock_post):
        """Test that title generation removes quotes."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"response": "\'Invoice 2024\'"}'
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        service = OllamaService(
            url="http://localhost:11434",
            endpoint="/api/generate",
            model="llama2"
        )

        title = service.generate_title(
            prompt="Generate title",
            content_for_id="Content"
        )

        # Quotes should be removed
        assert title == "Invoice 2024"
        assert '"' not in title
        assert "'" not in title

    @patch('src.llm.service.requests.post')
    def test_generate_title_strips_whitespace(self, mock_post):
        """Test that title generation strips whitespace."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"response": "  Invoice 2024  "}'
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        service = OllamaService(
            url="http://localhost:11434",
            endpoint="/api/generate",
            model="llama2"
        )

        title = service.generate_title(
            prompt="Generate title",
            content_for_id="Content"
        )

        # Whitespace should be stripped
        assert title == "Invoice 2024"
        assert title == title.strip()

    @patch('src.llm.service.requests.post')
    def test_generate_title_with_invalid_json(self, mock_post):
        """Test title generation with some invalid JSON lines."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''{"response": "Invoice"}
invalid json
{"response": " 2024-001"}'''
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        service = OllamaService(
            url="http://localhost:11434",
            endpoint="/api/generate",
            model="llama2"
        )

        title = service.generate_title(
            prompt="Generate title",
            content_for_id="Content"
        )

        # Should still parse valid JSON lines
        assert title == "Invoice 2024-001"

    @patch('src.llm.service.requests.post')
    def test_generate_title_on_request_exception(self, mock_post):
        """Test title generation when request fails."""
        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        service = OllamaService(
            url="http://localhost:11434",
            endpoint="/api/generate",
            model="llama2"
        )

        title = service.generate_title(
            prompt="Generate title",
            content_for_id="Content"
        )

        # Should return empty string on error
        assert title == ''

    @patch('src.llm.service.requests.post')
    def test_generate_title_payload_construction(self, mock_post):
        """Test that title generation payload is constructed correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"response": "Generated Title"}'
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        service = OllamaService(
            url="http://localhost:11434",
            endpoint="/api/generate",
            model="test-model"
        )

        service.generate_title(
            prompt="Generate a title",
            content_for_id="Some content"
        )

        # Verify payload
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['model'] == "test-model"
        assert payload['prompt'] == "Generate a title"


class TestEnsembleOllamaServiceInit:
    """Tests for EnsembleOllamaService initialization."""

    def test_init(self):
        """Test ensemble service initialization."""
        service1 = OllamaService("http://localhost:11434", "/api/generate", "llama2")
        service2 = OllamaService("http://localhost:11434", "/api/generate", "mistral")

        ensemble = EnsembleOllamaService(services=[service1, service2])

        assert len(ensemble.services) == 2
        assert ensemble.services[0].model == "llama2"
        assert ensemble.services[1].model == "mistral"

    def test_init_empty_services(self):
        """Test ensemble service with empty services list."""
        ensemble = EnsembleOllamaService(services=[])
        assert len(ensemble.services) == 0


class TestEnsembleOllamaServiceEvaluateContent:
    """Tests for EnsembleOllamaService.evaluate_content method."""

    @patch('src.llm.service.OllamaService.evaluate_content')
    def test_evaluate_content_consensus_high_quality(self, mock_evaluate):
        """Test ensemble evaluation with consensus for high quality."""
        # Mock all services returning "high quality"
        mock_evaluate.side_effect = ["high quality", "high quality", "high quality"]

        service1 = OllamaService("http://localhost:11434", "/api/generate", "llama2")
        service2 = OllamaService("http://localhost:11434", "/api/generate", "mistral")
        service3 = OllamaService("http://localhost:11434", "/api/generate", "gemma")

        ensemble = EnsembleOllamaService(services=[service1, service2, service3])

        result, consensus = ensemble.evaluate_content(
            content="Test content",
            prompt="Evaluate: ",
            document_id=123
        )

        assert result == "high quality"
        assert consensus is True
        assert mock_evaluate.call_count == 3

    @patch('src.llm.service.OllamaService.evaluate_content')
    def test_evaluate_content_consensus_low_quality(self, mock_evaluate):
        """Test ensemble evaluation with consensus for low quality."""
        mock_evaluate.side_effect = ["low quality", "low quality"]

        service1 = OllamaService("http://localhost:11434", "/api/generate", "llama2")
        service2 = OllamaService("http://localhost:11434", "/api/generate", "mistral")

        ensemble = EnsembleOllamaService(services=[service1, service2])

        result, consensus = ensemble.evaluate_content(
            content="Test content",
            prompt="Evaluate: ",
            document_id=456
        )

        assert result == "low quality"
        assert consensus is True

    @patch('src.llm.service.OllamaService.evaluate_content')
    def test_evaluate_content_no_consensus(self, mock_evaluate):
        """Test ensemble evaluation without consensus (tie)."""
        mock_evaluate.side_effect = ["high quality", "low quality"]

        service1 = OllamaService("http://localhost:11434", "/api/generate", "llama2")
        service2 = OllamaService("http://localhost:11434", "/api/generate", "mistral")

        ensemble = EnsembleOllamaService(services=[service1, service2])

        result, consensus = ensemble.evaluate_content(
            content="Test content",
            prompt="Evaluate: ",
            document_id=789
        )

        assert result == ''
        assert consensus is False

    @patch('src.llm.service.OllamaService.evaluate_content')
    def test_evaluate_content_majority_consensus(self, mock_evaluate):
        """Test ensemble evaluation with majority consensus."""
        # 2 high quality, 1 low quality -> should reach high quality consensus
        mock_evaluate.side_effect = ["high quality", "high quality", "low quality"]

        service1 = OllamaService("http://localhost:11434", "/api/generate", "llama2")
        service2 = OllamaService("http://localhost:11434", "/api/generate", "mistral")
        service3 = OllamaService("http://localhost:11434", "/api/generate", "gemma")

        ensemble = EnsembleOllamaService(services=[service1, service2, service3])

        result, consensus = ensemble.evaluate_content(
            content="Test content",
            prompt="Evaluate: ",
            document_id=100
        )

        assert result == "high quality"
        assert consensus is True

    @patch('src.llm.service.OllamaService.evaluate_content')
    def test_evaluate_content_with_empty_results(self, mock_evaluate):
        """Test ensemble evaluation when some services return empty results."""
        # One service returns empty string
        mock_evaluate.side_effect = ["high quality", "", "high quality"]

        service1 = OllamaService("http://localhost:11434", "/api/generate", "llama2")
        service2 = OllamaService("http://localhost:11434", "/api/generate", "mistral")
        service3 = OllamaService("http://localhost:11434", "/api/generate", "gemma")

        ensemble = EnsembleOllamaService(services=[service1, service2, service3])

        result, consensus = ensemble.evaluate_content(
            content="Test content",
            prompt="Evaluate: ",
            document_id=200
        )

        # Should reach consensus on "high quality" (2 out of 2 non-empty results)
        assert result == "high quality"
        assert consensus is True

    @patch('src.llm.service.OllamaService.evaluate_content')
    def test_evaluate_content_all_empty_results(self, mock_evaluate):
        """Test ensemble evaluation when all services return empty results."""
        mock_evaluate.side_effect = ["", "", ""]

        service1 = OllamaService("http://localhost:11434", "/api/generate", "llama2")
        service2 = OllamaService("http://localhost:11434", "/api/generate", "mistral")
        service3 = OllamaService("http://localhost:11434", "/api/generate", "gemma")

        ensemble = EnsembleOllamaService(services=[service1, service2, service3])

        result, consensus = ensemble.evaluate_content(
            content="Test content",
            prompt="Evaluate: ",
            document_id=300
        )

        assert result == ''
        assert consensus is False


class TestEnsembleOllamaServiceConsensusLogic:
    """Tests for EnsembleOllamaService.consensus_logic method."""

    def test_consensus_logic_unanimous_high_quality(self):
        """Test consensus logic with unanimous high quality."""
        service1 = OllamaService("http://localhost:11434", "/api/generate", "llama2")
        service2 = OllamaService("http://localhost:11434", "/api/generate", "mistral")

        ensemble = EnsembleOllamaService(services=[service1, service2])

        result, consensus = ensemble.consensus_logic(
            ["high quality", "high quality"]
        )

        assert result == "high quality"
        assert consensus is True

    def test_consensus_logic_unanimous_low_quality(self):
        """Test consensus logic with unanimous low quality."""
        service1 = OllamaService("http://localhost:11434", "/api/generate", "llama2")
        service2 = OllamaService("http://localhost:11434", "/api/generate", "mistral")

        ensemble = EnsembleOllamaService(services=[service1, service2])

        result, consensus = ensemble.consensus_logic(
            ["low quality", "low quality", "low quality"]
        )

        assert result == "low quality"
        assert consensus is True

    def test_consensus_logic_tie(self):
        """Test consensus logic with a tie (no majority)."""
        service1 = OllamaService("http://localhost:11434", "/api/generate", "llama2")
        service2 = OllamaService("http://localhost:11434", "/api/generate", "mistral")

        ensemble = EnsembleOllamaService(services=[service1, service2])

        result, consensus = ensemble.consensus_logic(
            ["high quality", "low quality"]
        )

        assert result == ''
        assert consensus is False

    def test_consensus_logic_three_way_tie(self):
        """Test consensus logic with a three-way tie."""
        service1 = OllamaService("http://localhost:11434", "/api/generate", "llama2")

        ensemble = EnsembleOllamaService(services=[service1])

        result, consensus = ensemble.consensus_logic(
            ["high quality", "low quality", "medium quality"]
        )

        assert result == ''
        assert consensus is False

    def test_consensus_logic_majority(self):
        """Test consensus logic with majority (not unanimous)."""
        service1 = OllamaService("http://localhost:11434", "/api/generate", "llama2")

        ensemble = EnsembleOllamaService(services=[service1])

        result, consensus = ensemble.consensus_logic(
            ["high quality", "high quality", "low quality", "low quality", "high quality"]
        )

        assert result == "high quality"
        assert consensus is True

    def test_consensus_logic_empty_results(self):
        """Test consensus logic with empty results list."""
        service1 = OllamaService("http://localhost:11434", "/api/generate", "llama2")

        ensemble = EnsembleOllamaService(services=[service1])

        result, consensus = ensemble.consensus_logic([])

        assert result == ''
        assert consensus is False

    def test_consensus_logic_single_result(self):
        """Test consensus logic with a single result."""
        service1 = OllamaService("http://localhost:11434", "/api/generate", "llama2")

        ensemble = EnsembleOllamaService(services=[service1])

        result, consensus = ensemble.consensus_logic(["high quality"])

        assert result == "high quality"
        assert consensus is True

    def test_consensus_logic_with_duplicates(self):
        """Test consensus logic handles duplicate results correctly."""
        service1 = OllamaService("http://localhost:11434", "/api/generate", "llama2")

        ensemble = EnsembleOllamaService(services=[service1])

        result, consensus = ensemble.consensus_logic(
            ["high quality", "high quality", "high quality", "low quality", "low quality"]
        )

        # high quality appears 3 times, low quality appears 2 times
        assert result == "high quality"
        assert consensus is True
