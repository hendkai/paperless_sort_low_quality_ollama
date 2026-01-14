"""Command-line interface for document quality analysis application."""

import sys
import time
import logging
from typing import Dict, List
from colorama import init, Fore, Style

# Initialize Colorama for colored output
init()

logger = logging.getLogger(__name__)


class CLIInterface:
    """Handles all command-line interface interactions and visual feedback."""

    # Color mapping for different message types
    COLORS = {
        'info': Fore.CYAN,
        'success': Fore.GREEN,
        'warning': Fore.YELLOW,
        'error': Fore.RED
    }

    def __init__(self):
        """Initialize CLI interface."""
        logger.info("CLI Interface initialized")

    def print_message(self, message: str, level: str = 'info') -> None:
        """Print message with specified color level.

        Args:
            message: The message to display.
            level: Color level ('info', 'success', 'warning', 'error').
        """
        color = self.COLORS.get(level, Fore.CYAN)
        print(f"{color}{message}{Style.RESET_ALL}")

    def show_robot_animation(self) -> None:
        """Display animated robot progress indicator."""
        frames = [
            f"{Fore.CYAN}🤖 Searching Documents {Fore.GREEN}[{Fore.YELLOW}═══════{Fore.GREEN}] |{Style.RESET_ALL}",
            f"{Fore.CYAN}🤖 Searching Documents {Fore.GREEN}[{Fore.YELLOW}═══════{Fore.GREEN}] /{Style.RESET_ALL}",
            f"{Fore.CYAN}🤖 Searching Documents {Fore.GREEN}[{Fore.YELLOW}═══════{Fore.GREEN}] -{Style.RESET_ALL}",
            f"{Fore.CYAN}🤖 Searching Documents {Fore.GREEN}[{Fore.YELLOW}═══════{Fore.GREEN}] \\{Style.RESET_ALL}"
        ]
        for frame in frames:
            sys.stdout.write('\r' + frame)
            sys.stdout.flush()
            time.sleep(0.2)

    def clear_animation(self) -> None:
        """Clear the animation line from terminal."""
        sys.stdout.write('\r' + ' ' * 50 + '\r')

    def show_welcome(self) -> None:
        """Display welcome message."""
        self.print_message("🤖 Welcome to the Document Quality Analyzer!")
        logger.info("Application started")

    def show_documents_found(self, count: int, documents: List[Dict]) -> None:
        """Display found documents info."""
        self.print_message(f"🤖 {count} documents with content found.")
        logger.info(f"Found {count} documents")
        for doc in documents:
            logger.info(f"Document ID: {doc.get('id')}, Title: {doc.get('title', 'No title')}")

    def show_no_documents(self) -> None:
        """Display message when no documents found."""
        self.print_message("🤖 No documents with content found.", 'warning')

    def confirm_processing(self, default: bool = True) -> bool:
        """Confirm processing with user."""
        self.print_message("🤖 Starting processing...")
        logger.info("User confirmed processing")
        return True

    def show_processing_aborted(self) -> None:
        """Display aborted processing message."""
        self.print_message("🤖 Processing aborted.", 'error')
        logger.info("Processing aborted")

    def show_processing_start(self, total: int) -> None:
        """Display start of processing."""
        self.print_message(f"🤖 Starting sequential processing of {total} documents...")
        logger.info(f"Starting processing of {total} documents")

    def show_document_progress(self, current: int, total: int, doc_id: int) -> None:
        """Display document processing progress."""
        self.print_message(f"🤖 Processing document {current}/{total} (ID: {doc_id})")
        logger.debug(f"Processing {current}/{total} (ID: {doc_id})")

    def show_document_complete(self, doc_id: int, current: int, total: int) -> None:
        """Display document completion."""
        self.print_message(f"✅ Document {doc_id} processed ({current}/{total})", 'success')

    def show_document_error(self, doc_id: int, error: str) -> None:
        """Display document processing error."""
        error_msg = str(error)[:100]
        self.print_message(f"❌ Error at document {doc_id}: {error_msg}...", 'error')

    def show_separator(self) -> None:
        """Display visual separator."""
        print(f"{Fore.YELLOW}{'=' * 80}{Style.RESET_ALL}\n")

    def show_processing_complete(self) -> None:
        """Display completion message."""
        self.print_message("🤖 Processing of all documents completed!", 'success')
        logger.info("Processing completed")

    def show_quality_decision(self, decision: str) -> None:
        """Display quality decision."""
        print(f"The AI models decided to classify the file as '{decision}'.")

    def show_rename_success(self, doc_id: int, old_title: str, new_title: str) -> None:
        """Display rename success."""
        self.print_message(
            f"✅ Document {doc_id} renamed from '{old_title}' to '{new_title}'", 'success'
        )
        logger.info(f"Document {doc_id} renamed from '{old_title}' to '{new_title}'")

    def show_rename_warning(self, desired_title: str, current_title: str) -> None:
        """Display rename warning."""
        self.print_message(
            f"⚠️ Rename possibly failed. Desired: '{desired_title}', Current: '{current_title}'",
            'warning'
        )

    def show_rename_error(self, doc_id: int, error: str) -> None:
        """Display rename error."""
        self.print_message(f"❌ Error renaming document {doc_id}: {error}", 'error')

    def show_consensus_not_reached(self, doc_id: int) -> None:
        """Display consensus failure."""
        self.print_message(
            f"AI models could not reach consensus for document {doc_id}. Skipping.",
            'warning'
        )
        logger.warning(f"No consensus for document {doc_id}")

    def show_statistics(self, stats: Dict[str, int]) -> None:
        """Display processing statistics."""
        print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📊 Processing Statistics{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        print(f"Total: {stats.get('total', 0)}")
        print(f"{Fore.GREEN}Processed: {stats.get('processed', 0)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Skipped: {stats.get('skipped', 0)}{Style.RESET_ALL}")
        print(f"{Fore.RED}Low quality: {stats.get('low_quality', 0)}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}High quality: {stats.get('high_quality', 0)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
        logger.info(f"Statistics: {stats}")
