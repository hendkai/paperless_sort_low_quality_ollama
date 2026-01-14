#!/usr/bin/env python3
"""Main entry point for Document Quality Analyzer using modular architecture.

This script orchestrates document quality analysis using a modular architecture
with dependency injection for better testability and maintainability.
"""

import logging
import os
import sys

from src.container import Container
from src.cli.interface import CLIInterface


# Configure logging from environment
from src.config.config import Config

LOG_LEVEL = Config.log_level()
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments.

    Returns:
        Namespace with parsed arguments. Currently supports --help only.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Welcome to Document Quality Analyzer - Analyze and tag documents by quality',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main_new.py              # Run with default settings from .env
  python main_new.py --help       # Show this help message

Environment Variables:
  API_URL, API_TOKEN             Paperless API connection details
  OLLAMA_URL, OLLAMA_ENDPOINT    Ollama LLM service configuration
  MODEL_NAME, SECOND_MODEL_NAME  LLM models to use for analysis
  LOW_QUALITY_TAG_ID             Tag ID for low quality documents
  HIGH_QUALITY_TAG_ID            Tag ID for high quality documents
  MAX_DOCUMENTS                  Maximum number of documents to process
  LOG_LEVEL                      Logging level (default: INFO)
        """
    )

    # No additional arguments yet, but argparse handles --help automatically
    return parser.parse_args()


def main() -> None:
    """Main entry point for the application.

    This function:
    1. Initializes the dependency injection container
    2. Fetches documents from Paperless
    3. Processes documents through quality analysis
    4. Tags and optionally renames documents based on quality
    """
    # Parse command line arguments (supports --help)
    args = parse_arguments()

    # Initialize container with dependency injection
    container = Container(validate_config=True)

    # Get CLI interface for user interaction
    cli = container.cli_interface

    # Show welcome message
    cli.show_welcome()

    # Fetch documents from Paperless API
    logger.info("Fetching documents from Paperless...")
    try:
        # Show robot animation while fetching
        cli.show_robot_animation()

        documents = container.api_client.fetch_documents(
            max_documents=container.config.max_documents()
        )

        # Clear animation
        cli.clear_animation()

        if documents:
            # Show found documents
            cli.show_documents_found(len(documents), documents)

            # Check if we should ignore already tagged documents
            ignore_already_tagged = os.getenv("IGNORE_ALREADY_TAGGED", "yes").lower() == 'yes'
            confirm = os.getenv("CONFIRM_PROCESS", "yes").lower()

            if confirm == "yes":
                # Show processing start
                total_to_process = len([d for d in documents if not (ignore_already_tagged and d.get('tags'))])
                cli.show_processing_start(total_to_process)

                # Process all documents
                stats = container.document_processor.process_documents(
                    documents=documents,
                    ignore_already_tagged=ignore_already_tagged
                )

                # Show completion
                cli.show_processing_complete()

                # Show statistics
                cli.show_statistics(stats)

            else:
                cli.show_processing_aborted()
        else:
            cli.show_no_documents()

    except Exception as e:
        logger.error(f"Error during document processing: {e}", exc_info=True)
        cli.print_message(f"❌ Error: {str(e)}", 'error')
        sys.exit(1)


if __name__ == "__main__":
    main()
