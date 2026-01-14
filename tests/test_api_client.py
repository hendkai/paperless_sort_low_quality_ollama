"""Unit tests for PaperlessClient module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from tenacity import RetryError

from src.api.client import PaperlessClient


class TestPaperlessClientInit:
    """Tests for PaperlessClient initialization."""

    def test_init(self):
        """Test client initialization with correct parameters."""
        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token_123"
        )
        assert client.api_url == "http://localhost:8000"
        assert client.api_token == "test_token_123"

    def test_init_with_different_url(self):
        """Test client initialization with different API URL."""
        client = PaperlessClient(
            api_url="https://paperless.example.com",
            api_token="another_token"
        )
        assert client.api_url == "https://paperless.example.com"
        assert client.api_token == "another_token"


class TestGetHeaders:
    """Tests for _get_headers method."""

    def test_get_headers(self):
        """Test that headers are generated correctly."""
        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="secret_token"
        )
        headers = client._get_headers()
        assert headers == {'Authorization': 'Token secret_token'}


class TestFetchDocuments:
    """Tests for fetch_documents method."""

    @patch('src.api.client.requests.get')
    def test_fetch_documents_success(self, mock_get):
        """Test successful document fetching."""
        # Mock the response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [
                {'id': 1, 'title': 'Doc 1', 'content': 'Content 1'},
                {'id': 2, 'title': 'Doc 2', 'content': 'Content 2'}
            ],
            'next': None
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        documents = client.fetch_documents(max_documents=10)

        assert len(documents) == 2
        assert documents[0]['id'] == 1
        assert documents[1]['id'] == 2
        mock_get.assert_called_once()

    @patch('src.api.client.requests.get')
    def test_fetch_documents_filters_empty_content(self, mock_get):
        """Test that documents with empty content are filtered out."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [
                {'id': 1, 'title': 'Doc 1', 'content': 'Valid content'},
                {'id': 2, 'title': 'Doc 2', 'content': '   '},  # Whitespace only
                {'id': 3, 'title': 'Doc 3', 'content': ''},  # Empty
                {'id': 4, 'title': 'Doc 4', 'content': 'Another valid'}
            ],
            'next': None
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        documents = client.fetch_documents(max_documents=10)

        # Should only return documents with non-empty content
        assert len(documents) == 2
        assert documents[0]['id'] == 1
        assert documents[1]['id'] == 4

    @patch('src.api.client.requests.get')
    def test_fetch_documents_with_pagination(self, mock_get):
        """Test document fetching with pagination."""
        # First page
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            'results': [
                {'id': 1, 'title': 'Doc 1', 'content': 'Content 1'},
                {'id': 2, 'title': 'Doc 2', 'content': 'Content 2'}
            ],
            'next': 'http://localhost:8000/documents/?page=2&page_size=100'
        }
        mock_response1.raise_for_status = Mock()

        # Second page
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            'results': [
                {'id': 3, 'title': 'Doc 3', 'content': 'Content 3'}
            ],
            'next': None
        }
        mock_response2.raise_for_status = Mock()

        mock_get.side_effect = [mock_response1, mock_response2]

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        documents = client.fetch_documents(max_documents=10, page_size=2)

        assert len(documents) == 3
        assert mock_get.call_count == 2

    @patch('src.api.client.requests.get')
    def test_fetch_documents_respects_max_documents(self, mock_get):
        """Test that max_documents limit is respected."""
        mock_response = Mock()
        mock_response.status_code = 200
        # Return more documents than max_documents
        mock_response.json.return_value = {
            'results': [
                {'id': i, 'title': f'Doc {i}', 'content': f'Content {i}'}
                for i in range(1, 151)  # 150 documents
            ],
            'next': None
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        documents = client.fetch_documents(max_documents=50)

        # Should only return 50 despite having 150 available
        assert len(documents) == 50

    @patch('src.api.client.requests.get')
    def test_fetch_documents_retry_on_failure(self, mock_get):
        """Test that fetch_documents retries on API failure."""
        # First two calls fail, third succeeds
        mock_fail = Mock()
        mock_fail.raise_for_status.side_effect = requests.exceptions.RequestException("API Error")

        mock_success = Mock()
        mock_success.status_code = 200
        mock_success.json.return_value = {
            'results': [{'id': 1, 'title': 'Doc 1', 'content': 'Content 1'}],
            'next': None
        }
        mock_success.raise_for_status = Mock()

        mock_get.side_effect = [mock_fail, mock_fail, mock_success]

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        documents = client.fetch_documents(max_documents=10)

        assert len(documents) == 1
        assert mock_get.call_count == 3

    @patch('src.api.client.requests.get')
    def test_fetch_documents_custom_page_size(self, mock_get):
        """Test fetch_documents with custom page size."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [{'id': 1, 'title': 'Doc 1', 'content': 'Content 1'}],
            'next': None
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        client.fetch_documents(max_documents=10, page_size=50)

        # Check that page_size parameter was passed correctly
        call_args = mock_get.call_args
        assert 'params' in call_args[1]
        assert call_args[1]['params']['page_size'] == 50


class TestGetCSRFToken:
    """Tests for get_csrf_token method."""

    @patch('src.api.client.requests.Session')
    def test_get_csrf_token_success(self, mock_session_class):
        """Test successful CSRF token retrieval."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.cookies.get.return_value = 'csrf_token_123'
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        token = client.get_csrf_token(mock_session)

        assert token == 'csrf_token_123'
        mock_session.get.assert_called_once()

    @patch('src.api.client.requests.Session')
    def test_get_csrf_token_missing_token(self, mock_session_class):
        """Test that ValueError is raised when CSRF token is missing."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.cookies.get.return_value = None  # No token
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        with pytest.raises(ValueError, match="CSRF Token not found"):
            client.get_csrf_token(mock_session)


class TestGetDocument:
    """Tests for get_document method."""

    @patch('src.api.client.requests.get')
    def test_get_document_success(self, mock_get):
        """Test successful document details fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 123,
            'title': 'Test Document',
            'content': 'Test content',
            'tags': [1, 2]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        document = client.get_document(123)

        assert document['id'] == 123
        assert document['title'] == 'Test Document'
        assert document['content'] == 'Test content'
        assert document['tags'] == [1, 2]

    @patch('src.api.client.requests.get')
    def test_get_document_no_retry_with_exception_handler(self, mock_get):
        """Test that get_document returns empty dict when exception is caught.

        Note: The try-except block in get_document catches RequestException
        before the retry decorator can handle it, so no retry occurs.
        """
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        document = client.get_document(123)

        # After the exception is caught, returns empty dict
        assert document == {}
        # Only one call is made because the exception is caught
        assert mock_get.call_count == 1

    @patch('src.api.client.requests.get')
    def test_get_document_returns_empty_dict_on_error(self, mock_get):
        """Test that get_document returns empty dict when all retries fail."""
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        document = client.get_document(123)

        # After all retries fail, should return empty dict
        assert document == {}


class TestTagDocument:
    """Tests for tag_document method."""

    @patch('src.api.client.requests.get')
    @patch('src.api.client.requests.patch')
    def test_tag_document_add_new_tag(self, mock_patch, mock_get):
        """Test adding a new tag to a document."""
        # Mock GET request to fetch current tags
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {'tags': [1, 2]}
        mock_get_response.raise_for_status = Mock()
        mock_get.return_value = mock_get_response

        # Mock PATCH request to add tag
        mock_patch_response = Mock()
        mock_patch_response.status_code = 200
        mock_patch_response.text = '{"status": "success"}'
        mock_patch_response.raise_for_status = Mock()
        mock_patch.return_value = mock_patch_response

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        client.tag_document(document_id=123, tag_id=3, csrf_token='csrf_token')

        # Verify GET was called to check existing tags
        mock_get.assert_called_once()
        # Verify PATCH was called to add the new tag
        mock_patch.assert_called_once()
        call_args = mock_patch.call_args
        assert call_args[1]['json'] == {"tags": [1, 2, 3]}

    @patch('src.api.client.requests.get')
    @patch('src.api.client.requests.patch')
    def test_tag_document_already_tagged(self, mock_patch, mock_get):
        """Test that tag_document skips if document already has the tag."""
        # Mock GET request showing document already has tag 3
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {'tags': [1, 2, 3]}
        mock_get_response.raise_for_status = Mock()
        mock_get.return_value = mock_get_response

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        client.tag_document(document_id=123, tag_id=3, csrf_token='csrf_token')

        # GET should be called to check existing tags
        mock_get.assert_called_once()
        # PATCH should NOT be called since tag already exists
        mock_patch.assert_not_called()

    @patch('src.api.client.requests.get')
    @patch('src.api.client.requests.patch')
    def test_tag_document_retry_on_failure(self, mock_patch, mock_get):
        """Test that tag_document retries on failure."""
        # Mock GET request
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {'tags': [1, 2]}
        mock_get_response.raise_for_status = Mock()
        mock_get.return_value = mock_get_response

        # Mock PATCH requests - first two fail, third succeeds
        mock_fail = Mock()
        mock_fail.raise_for_status.side_effect = requests.exceptions.RequestException("API Error")

        mock_success = Mock()
        mock_success.status_code = 200
        mock_success.text = '{"status": "success"}'
        mock_success.raise_for_status = Mock()

        mock_patch.side_effect = [mock_fail, mock_fail, mock_success]

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        client.tag_document(document_id=123, tag_id=3, csrf_token='csrf_token')

        # Should retry 3 times total
        assert mock_patch.call_count == 3


class TestUpdateTitle:
    """Tests for update_title method."""

    @patch('src.api.client.requests.get')
    @patch('src.api.client.requests.patch')
    def test_update_title_success(self, mock_patch, mock_get):
        """Test successful title update."""
        # Mock PATCH request for updating
        mock_patch_response = Mock()
        mock_patch_response.status_code = 200
        mock_patch_response.raise_for_status = Mock()
        mock_patch.return_value = mock_patch_response

        # Mock GET request for verification (called by get_document)
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            'id': 123,
            'title': 'New Title'  # Verified title matches
        }
        mock_get_response.raise_for_status = Mock()
        mock_get.return_value = mock_get_response

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        result = client.update_title(123, 'New Title', 'csrf_token')

        assert result is True
        mock_patch.assert_called_once()
        call_args = mock_patch.call_args
        assert call_args[1]['json'] == {"title": "New Title"}

    @patch('src.api.client.requests.get')
    @patch('src.api.client.requests.patch')
    def test_update_title_verification_fails(self, mock_patch, mock_get):
        """Test update_title when verification fails."""
        # Mock PATCH request for updating
        mock_patch_response = Mock()
        mock_patch_response.status_code = 200
        mock_patch_response.raise_for_status = Mock()
        mock_patch.return_value = mock_patch_response

        # Mock GET request for verification - returns different title
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            'id': 123,
            'title': 'Old Title'  # Verification fails - title doesn't match
        }
        mock_get_response.raise_for_status = Mock()
        mock_get.return_value = mock_get_response

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        result = client.update_title(123, 'New Title', 'csrf_token')

        assert result is False

    @patch('src.api.client.requests.get')
    @patch('src.api.client.requests.patch')
    def test_update_title_retry_on_failure(self, mock_patch, mock_get):
        """Test that update_title retries on PATCH failure."""
        # Mock PATCH requests - first two fail, third succeeds
        mock_fail = Mock()
        mock_fail.raise_for_status.side_effect = requests.exceptions.RequestException("API Error")

        mock_success = Mock()
        mock_success.status_code = 200
        mock_success.raise_for_status = Mock()

        mock_patch.side_effect = [mock_fail, mock_fail, mock_success]

        # Mock GET for verification
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {'id': 123, 'title': 'New Title'}
        mock_get_response.raise_for_status = Mock()
        mock_get.return_value = mock_get_response

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        result = client.update_title(123, 'New Title', 'csrf_token')

        assert result is True
        assert mock_patch.call_count == 3

    @patch('src.api.client.requests.get')
    @patch('src.api.client.requests.patch')
    def test_update_title_raises_exception_on_error(self, mock_patch, mock_get):
        """Test that update_title raises RetryError after all retries fail."""
        mock_patch.side_effect = requests.exceptions.RequestException("API Error")

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        # tenacity wraps the exception in RetryError after all retries fail
        from tenacity import RetryError
        with pytest.raises(RetryError):
            client.update_title(123, 'New Title', 'csrf_token')


class TestHeadersWithCSRF:
    """Tests for headers with CSRF token."""

    @patch('src.api.client.requests.patch')
    @patch('src.api.client.requests.get')
    def test_tag_document_includes_csrf_header(self, mock_get, mock_patch):
        """Test that tag_document includes CSRF token in headers."""
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {'tags': [1]}
        mock_get_response.raise_for_status = Mock()
        mock_get.return_value = mock_get_response

        mock_patch_response = Mock()
        mock_patch_response.status_code = 200
        mock_patch_response.raise_for_status = Mock()
        mock_patch.return_value = mock_patch_response

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        client.tag_document(123, 2, 'test_csrf_token')

        # Check that CSRF token is in headers
        call_args = mock_patch.call_args
        headers = call_args[1]['headers']
        assert 'X-CSRFToken' in headers
        assert headers['X-CSRFToken'] == 'test_csrf_token'
        assert headers['Content-Type'] == 'application/json'

    @patch('src.api.client.requests.patch')
    @patch('src.api.client.requests.get')
    def test_update_title_includes_csrf_header(self, mock_get, mock_patch):
        """Test that update_title includes CSRF token in headers."""
        mock_patch_response = Mock()
        mock_patch_response.status_code = 200
        mock_patch_response.raise_for_status = Mock()
        mock_patch.return_value = mock_patch_response

        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {'id': 123, 'title': 'New Title'}
        mock_get_response.raise_for_status = Mock()
        mock_get.return_value = mock_get_response

        client = PaperlessClient(
            api_url="http://localhost:8000",
            api_token="test_token"
        )

        client.update_title(123, 'New Title', 'test_csrf_token')

        # Check that CSRF token is in headers
        call_args = mock_patch.call_args
        headers = call_args[1]['headers']
        assert 'X-CSRFToken' in headers
        assert headers['X-CSRFToken'] == 'test_csrf_token'
        assert headers['Content-Type'] == 'application/json'
