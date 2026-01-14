#!/usr/bin/env python3
"""
Demo script showing the structure of progress_state.json after processing documents.

This demonstrates what the state file looks like after processing MAX_DOCUMENTS=3.
"""

import json
import os
import time
from datetime import datetime
from progress_tracker import ProgressTracker

def demo_progress_state():
    """Create and display a sample progress state file."""

    print("=" * 80)
    print("DEMO: Progress State File Structure")
    print("=" * 80)

    demo_file = "demo_progress_state.json"

    # Clean up any existing demo file
    if os.path.exists(demo_file):
        os.remove(demo_file)

    # Initialize tracker and process sample documents
    tracker = ProgressTracker(demo_file)

    print("\nSimulating processing of 3 documents (MAX_DOCUMENTS=3)...\n")

    # Document 1: High quality with title change
    print("1. Processing document ID 1001 (Invoice_2024_001.pdf)...")
    tracker.save_checkpoint(
        document_id=1001,
        quality_response='high quality',
        consensus_reached=True,
        new_title='Invoice_2024_001.pdf',
        error=None,
        processing_time=2.35
    )
    time.sleep(0.1)

    # Document 2: Low quality
    print("2. Processing document ID 1002 (Unknown_Document.pdf)...")
    tracker.save_checkpoint(
        document_id=1002,
        quality_response='low quality',
        consensus_reached=True,
        new_title=None,
        error=None,
        processing_time=1.87
    )
    time.sleep(0.1)

    # Document 3: High quality with consensus
    print("3. Processing document ID 1003 (scan_0045.pdf)...")
    tracker.save_checkpoint(
        document_id=1003,
        quality_response='high quality',
        consensus_reached=True,
        new_title='Contract_Services_2024.pdf',
        error=None,
        processing_time=3.12
    )

    print("\n" + "=" * 80)
    print("PROGRESS STATE FILE CREATED: demo_progress_state.json")
    print("=" * 80)

    # Read and display the file
    with open(demo_file, 'r') as f:
        state = json.load(f)

    print("\nFile Structure:")
    print(json.dumps(state, indent=2))

    print("\n" + "=" * 80)
    print("VERIFICATION CHECKLIST")
    print("=" * 80)

    checks = [
        ("✓", "State file created", os.path.exists(demo_file)),
        ("✓", "Contains 'created_at' timestamp", 'created_at' in state),
        ("✓", "Contains 'last_updated' timestamp", 'last_updated' in state),
        ("✓", "Contains 'documents' array", 'documents' in state),
        ("✓", f"Contains 3 processed documents", len(state.get('documents', [])) == 3),
        ("✓", "Document 1 has all required fields", all(k in state['documents'][0] for k in
            ['document_id', 'quality_response', 'consensus_reached', 'new_title', 'error', 'processing_time', 'processed_at'])),
        ("✓", "Document 2 has all required fields", all(k in state['documents'][1] for k in
            ['document_id', 'quality_response', 'consensus_reached', 'new_title', 'error', 'processing_time', 'processed_at'])),
        ("✓", "Document 3 has all required fields", all(k in state['documents'][2] for k in
            ['document_id', 'quality_response', 'consensus_reached', 'new_title', 'error', 'processing_time', 'processed_at'])),
        ("✓", "Timestamps are valid ISO format", all(datetime.fromisoformat(doc['processed_at']) for doc in state['documents'])),
        ("✓", "Processing times are recorded", all(doc.get('processing_time', 0) > 0 for doc in state['documents'])),
    ]

    for symbol, description, passed in checks:
        status = symbol if passed else "✗"
        print(f"{status} {description}")

    print("\n" + "=" * 80)
    print("PROGRESS SUMMARY")
    print("=" * 80)

    summary = tracker.get_progress_summary()
    print(f"\nTotal Documents Processed: {summary['total_processed']}")
    print(f"Consensus Reached: {summary['consensus_count']}")
    print(f"Errors: {summary['error_count']}")
    print(f"Total Processing Time: {summary['total_processing_time']:.2f} seconds")
    print(f"State Created At: {summary['created_at']}")
    print(f"Last Updated: {summary['last_updated']}")

    print("\n" + "=" * 80)
    print("✓ DEMO COMPLETE")
    print("=" * 80)
    print(f"\nThe demo progress state file has been saved to: {demo_file}")
    print("You can examine it to see the exact structure that will be created")
    print("when running the main application with MAX_DOCUMENTS=3.")

    return True

if __name__ == "__main__":
    demo_progress_state()
