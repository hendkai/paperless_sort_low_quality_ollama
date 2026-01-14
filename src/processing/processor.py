"""Document processor for orchestrating document quality analysis and tagging."""

import logging
import time
import requests
from typing import List, Dict
from src.api.client import PaperlessClient
from src.quality.analyzer import QualityAnalyzer
from src.llm.service import OllamaService


logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Orchestrates document processing: quality evaluation, tagging, and renaming."""

    def __init__(
        self,
        api_client: PaperlessClient,
        quality_analyzer: QualityAnalyzer,
        llm_service: OllamaService,
        low_quality_tag_id: int,
        high_quality_tag_id: int,
        rename_documents: bool = False
    ) -> None:
        """Initialize DocumentProcessor with dependencies."""
        self.api_client = api_client
        self.quality_analyzer = quality_analyzer
        self.llm_service = llm_service
        self.low_quality_tag_id = low_quality_tag_id
        self.high_quality_tag_id = high_quality_tag_id
        self.rename_documents = rename_documents
        logger.info(f"DocumentProcessor initialized (low_tag: {low_quality_tag_id}, "
                   f"high_tag: {high_quality_tag_id}, rename: {rename_documents})")

    def process_documents(
        self,
        documents: List[Dict],
        ignore_already_tagged: bool = True
    ) -> Dict[str, int]:
        """Process documents and tag based on quality. Returns statistics dict."""
        session = requests.Session()
        csrf_token = self.api_client.get_csrf_token(session)

        documents_to_process = documents if not ignore_already_tagged else [
            doc for doc in documents if not doc.get('tags')
        ]

        total = len(documents_to_process)
        logger.info(f"Starting processing of {total} documents")

        stats = {'total': total, 'processed': 0, 'skipped': 0,
                 'low_quality': 0, 'high_quality': 0}

        for idx, document in enumerate(documents_to_process, 1):
            doc_id = document.get('id')
            logger.info(f"Processing document {idx}/{total} (ID: {doc_id})")

            try:
                result = self._process_single_document(document, document.get('content', ''), csrf_token)
                if result == 'tagged_low':
                    stats['low_quality'] += 1
                    stats['processed'] += 1
                elif result == 'tagged_high':
                    stats['high_quality'] += 1
                    stats['processed'] += 1
                elif result == 'skipped':
                    stats['skipped'] += 1
                logger.info(f"Document {doc_id} processed ({idx}/{total} complete)")
            except Exception as e:
                logger.error(f"Error processing document {doc_id}: {e}")
                stats['skipped'] += 1

            time.sleep(1)

        logger.info(f"Processing completed. Stats: {stats}")
        return stats

    def _process_single_document(self, document: Dict, content: str, csrf_token: str) -> str:
        """Process single document: evaluate quality, tag, and optionally rename."""
        doc_id = document.get('id')
        logger.info(f"Processing document ID: {doc_id}, title: '{document.get('title')}', "
                   f"content_length: {len(content)}")

        quality_result, consensus_reached = self.quality_analyzer.evaluate(content, doc_id)
        action, should_process = self.quality_analyzer.determine_tag_action(
            quality_result, consensus_reached
        )

        if not should_process:
            logger.info(f"Skipping document {doc_id} (action: {action})")
            return 'skipped'

        if action == 'tag_low':
            self.api_client.tag_document(doc_id, self.low_quality_tag_id, csrf_token)
            logger.info(f"Document {doc_id} tagged as low quality")
            return 'tagged_low'
        elif action == 'tag_high':
            self.api_client.tag_document(doc_id, self.high_quality_tag_id, csrf_token)
            logger.info(f"Document {doc_id} tagged as high quality")
            if self.rename_documents:
                self._rename_document(doc_id, csrf_token, document)
            return 'tagged_high'

        return 'skipped'

    def _rename_document(self, doc_id: int, csrf_token: str, document: Dict) -> None:
        """Generate and apply new title for high quality document."""
        logger.info(f"Starting rename process for document {doc_id}")
        details = self.api_client.get_document(doc_id)
        if not details:
            logger.warning(f"Could not fetch details for document {doc_id}")
            return

        old_title = details.get('title', '')
        new_title = self._generate_title(details.get('content', ''))
        logger.info(f"Renaming document {doc_id} from '{old_title}' to '{new_title}'")

        try:
            success = self.api_client.update_title(doc_id, new_title, csrf_token)
            if success:
                logger.info(f"Document {doc_id} successfully renamed")
            else:
                logger.warning(f"Title update verification failed for document {doc_id}")
        except Exception as e:
            logger.error(f"Error renaming document {doc_id}: {e}")

    def _generate_title(self, content: str) -> str:
        """Generate meaningful title for document content (max 100 chars)."""
        if not content:
            return "Untitled Document"

        truncated = content[:1000]
        logger.info(f"Using first {len(truncated)} chars for title generation")

        title_prompt = f"""Du bist ein Experte für die Erstellung sinnvoller Dokumenttitel.
Analysiere den folgenden Inhalt und erstelle einen prägnanten, aussagekräftigen Titel,
der den Inhalt treffend zusammenfasst. Der Titel sollte nicht länger als 100 Zeichen sein.
Antworte nur mit dem Titel, ohne Erklärung oder zusätzlichen Text.

Inhalt:
{truncated}
"""

        try:
            title = self.llm_service.generate_title(title_prompt, truncated)
            if not title or not title.strip():
                logger.warning("LLM returned no title, using fallback")
                title = " ".join(content.split()[:5])
            title = title.replace("\n", " ").strip()
            if len(title) > 100:
                title = title[:97] + "..."
            logger.info(f"Generated title: '{title}'")
            return title
        except Exception as e:
            logger.error(f"Error in LLM title generation: {e}")
            return " ".join(content.split()[:5]).replace("\n", " ").strip()[:100]
