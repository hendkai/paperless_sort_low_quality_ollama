"""Paperless API client for interacting with Paperless-ngx API."""

import logging
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_fixed
import requests


logger = logging.getLogger(__name__)


class PaperlessClient:
    """Client for interacting with Paperless-ngx API."""

    def __init__(self, api_url: str, api_token: str) -> None:
        """Initialize the Paperless API client.

        Args:
            api_url: Base URL of the Paperless API (e.g., 'http://localhost:8000').
            api_token: Authentication token for API requests.
        """
        self.api_url = api_url
        self.api_token = api_token
        logger.info(f"PaperlessClient initialized with API URL: {api_url}")

    def _get_headers(self) -> dict:
        """Get standard headers for API requests."""
        return {'Authorization': f'Token {self.api_token}'}

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def fetch_documents(self, max_documents: int = 100, page_size: int = 100) -> list:
        """Fetch documents with content from Paperless.

        Args:
            max_documents: Maximum number of documents to retrieve.
            page_size: Number of documents per page in pagination.

        Returns:
            List of document dictionaries with id, title, content, and metadata.
        """
        headers = self._get_headers()
        params = {'page_size': page_size}
        documents = []
        total_collected = 0

        logger.info(f"Fetching documents (max: {max_documents})...")

        while True:
            response = requests.get(f'{self.api_url}/documents/', headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            new_docs = data.get('results', [])

            # Only include documents with non-empty content
            documents.extend([doc for doc in new_docs if doc.get('content', '').strip()])
            total_collected += len(new_docs)

            if total_collected >= max_documents or not data.get('next'):
                break
            else:
                # Extract page number from next URL
                params['page'] = data['next'].split('page=')[1].split('&')[0]

        logger.info(f"Fetched {len(documents[:max_documents])} documents with content")
        return documents[:max_documents]

    def get_csrf_token(self, session: requests.Session) -> Optional[str]:
        """Get CSRF token from the API.

        Args:
            session: Requests session to store cookies.

        Returns:
            CSRF token string.

        Raises:
            ValueError: If CSRF token is not found in response cookies.
        """
        headers = self._get_headers()
        response = session.get(self.api_url, headers=headers)
        response.raise_for_status()
        csrf_token = response.cookies.get('csrftoken')

        if not csrf_token:
            raise ValueError("CSRF Token not found in response cookies.")

        logger.info(f"CSRF Token retrieved: {csrf_token}")
        return csrf_token

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_document(self, document_id: int) -> dict:
        """Fetch detailed information for a specific document.

        Args:
            document_id: ID of the document to fetch.

        Returns:
            Dictionary with document details including content, metadata, and tags.
        """
        headers = self._get_headers()

        try:
            logger.info(f"Fetching details for document ID {document_id}...")
            response = requests.get(f'{self.api_url}/documents/{document_id}/', headers=headers)
            response.raise_for_status()
            document_data = response.json()
            logger.info(f"Successfully fetched details for document ID {document_id}")
            return document_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching details for document ID {document_id}: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Server response: {e.response.text}")
            return {}

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def tag_document(self, document_id: int, tag_id: int, csrf_token: str) -> None:
        """Add a tag to a document if not already tagged.

        Args:
            document_id: ID of the document to tag.
            tag_id: ID of the tag to add.
            csrf_token: CSRF token for the request.
        """
        headers = {
            **self._get_headers(),
            'X-CSRFToken': csrf_token,
            'Content-Type': 'application/json'
        }

        url = f'{self.api_url}/documents/{document_id}/'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        existing_tags = response.json().get('tags', [])

        if tag_id not in existing_tags:
            payload = {"tags": existing_tags + [tag_id]}
            response = requests.patch(url, json=payload, headers=headers)
            logger.info(f"Tagging Response: {response.status_code} - {response.text}")
            response.raise_for_status()
            logger.info(f"Successfully tagged document {document_id} with tag ID {tag_id}")
        else:
            logger.info(f"Document {document_id} already has tag ID {tag_id}")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def update_title(self, document_id: int, new_title: str, csrf_token: str) -> bool:
        """Update the title of a document.

        Args:
            document_id: ID of the document to update.
            new_title: New title for the document.
            csrf_token: CSRF token for the request.

        Returns:
            True if update was successful, False otherwise.

        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        headers = {
            **self._get_headers(),
            'X-CSRFToken': csrf_token,
            'Content-Type': 'application/json'
        }

        payload = {"title": new_title}

        try:
            logger.info(f"Updating title for document {document_id} to: {new_title}")
            response = requests.patch(
                f'{self.api_url}/documents/{document_id}/',
                json=payload,
                headers=headers
            )
            response.raise_for_status()

            # Verify the update was successful
            details = self.get_document(document_id)
            current_title = details.get('title', '')

            if current_title == new_title:
                logger.info(f"Successfully updated title for document {document_id}")
                return True
            else:
                logger.warning(
                    f"Title update verification failed for document {document_id}. "
                    f"Expected: '{new_title}', Got: '{current_title}'"
                )
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating title for document {document_id}: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Server response: {e.response.text}")
            raise
