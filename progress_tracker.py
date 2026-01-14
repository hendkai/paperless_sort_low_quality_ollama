import json
import os
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Tracks document processing progress with persistent state storage.

    Manages checkpoint-based progress tracking to allow resumption
    of document processing after interruptions.
    """

    def __init__(self, state_file_path: str) -> None:
        """
        Initialize the ProgressTracker with a state file path.

        Args:
            state_file_path: Path to the JSON file where state will be stored
        """
        self.state_file_path = state_file_path
        self.state: Dict[str, Any] = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """
        Load state from file or create new state structure.

        Returns:
            Dictionary containing the loaded state or a new empty state
        """
        try:
            if os.path.exists(self.state_file_path):
                logger.info(f"Loading existing state from {self.state_file_path}")
                with open(self.state_file_path, 'r') as f:
                    state = json.load(f)
                    logger.info(f"Loaded state with {len(state.get('documents', []))} processed documents")
                    return state
            else:
                logger.info(f"No existing state file found at {self.state_file_path}. Creating new state.")
                return self._create_new_state()
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from state file {self.state_file_path}: {e}")
            logger.info("Creating new state to recover from corrupted file")
            return self._create_new_state()
        except Exception as e:
            logger.error(f"Unexpected error loading state file {self.state_file_path}: {e}")
            logger.info("Creating new state to recover from error")
            return self._create_new_state()

    def _create_new_state(self) -> Dict[str, Any]:
        """
        Create a new empty state structure.

        Returns:
            Dictionary with empty state structure
        """
        return {
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'documents': []
        }

    def _save_state(self) -> None:
        """
        Save current state to file.
        """
        try:
            self.state['last_updated'] = datetime.now().isoformat()
            with open(self.state_file_path, 'w') as f:
                json.dump(self.state, f, indent=2)
            logger.debug(f"State saved to {self.state_file_path}")
        except Exception as e:
            logger.error(f"Error saving state to {self.state_file_path}: {e}")
            raise

    def save_checkpoint(
        self,
        document_id: int,
        quality_response: str,
        consensus_reached: bool,
        new_title: Optional[str],
        error: Optional[str],
        processing_time: float
    ) -> None:
        """
        Save a processing checkpoint for a document.

        Args:
            document_id: The ID of the processed document
            quality_response: The quality assessment result (e.g., 'high quality', 'low quality')
            consensus_reached: Whether the ensemble models reached consensus
            new_title: The new title generated for the document (if any)
            error: Any error that occurred during processing (if any)
            processing_time: Time taken to process the document in seconds
        """
        document_entry = {
            'document_id': document_id,
            'quality_response': quality_response,
            'consensus_reached': consensus_reached,
            'new_title': new_title,
            'error': error,
            'processing_time': processing_time,
            'processed_at': datetime.now().isoformat()
        }

        self.state['documents'].append(document_entry)
        self._save_state()
        logger.info(f"Checkpoint saved for document ID {document_id}")

    def is_processed(self, document_id: int) -> bool:
        """
        Check if a document has already been processed.

        Args:
            document_id: The ID of the document to check

        Returns:
            True if the document has been processed, False otherwise
        """
        for doc in self.state['documents']:
            if doc['document_id'] == document_id:
                return True
        return False

    def load_checkpoint(self, document_id: int) -> Optional[Dict[str, Any]]:
        """
        Load checkpoint data for a specific document.

        Args:
            document_id: The ID of the document to load

        Returns:
            Dictionary containing the checkpoint data if found, None otherwise
        """
        for doc in self.state['documents']:
            if doc['document_id'] == document_id:
                logger.debug(f"Checkpoint loaded for document ID {document_id}")
                return doc
        logger.debug(f"No checkpoint found for document ID {document_id}")
        return None
