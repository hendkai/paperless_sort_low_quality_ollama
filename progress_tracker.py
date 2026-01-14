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
