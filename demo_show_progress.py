#!/usr/bin/env python3
"""
Visual demo of --show-progress functionality.

This script demonstrates how the --show-progress command displays
accurate summaries of document processing progress.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from progress_tracker import ProgressTracker

def create_demo_state():
    """Create a demo state file with sample processing data."""
    state_file = "demo_progress_state.json"

    # Clean up any existing demo file
    if os.path.exists(state_file):
        os.remove(state_file)

    print("=" * 80)
    print("DEMO: Creating sample processing state...")
    print("=" * 80)
    print()

    # Create ProgressTracker
    pt = ProgressTracker(state_file)

    # Simulate processing various documents
    demo_documents = [
        {
            'document_id': 1001,
            'quality': 'high quality',
            'consensus': True,
            'title': 'Invoice_2024_001.pdf',
            'error': None,
            'time': 2.35,
            'description': 'Invoice document - successfully processed and renamed'
        },
        {
            'document_id': 1002,
            'quality': 'low quality',
            'consensus': True,
            'title': None,
            'error': None,
            'time': 1.85,
            'description': 'Low quality document - tagged correctly'
        },
        {
            'document_id': 1003,
            'quality': 'high quality',
            'consensus': True,
            'title': 'Contract_Amendment.pdf',
            'error': None,
            'time': 3.12,
            'description': 'Contract document - successfully processed and renamed'
        },
        {
            'document_id': 1004,
            'quality': '',
            'consensus': False,
            'title': None,
            'error': '404 Client Error: Not Found',
            'time': 0.55,
            'description': 'Error during processing - document not found'
        },
        {
            'document_id': 1005,
            'quality': 'high quality',
            'consensus': True,
            'title': 'Meeting_Minutes_Q1.pdf',
            'error': None,
            'time': 2.78,
            'description': 'Meeting minutes - successfully processed and renamed'
        },
        {
            'document_id': 1006,
            'quality': 'low quality',
            'consensus': True,
            'title': None,
            'error': None,
            'time': 1.42,
            'description': 'Another low quality document - tagged correctly'
        },
        {
            'document_id': 1007,
            'quality': 'high quality',
            'consensus': True,
            'title': 'Annual_Report_2023.pdf',
            'error': None,
            'time': 4.15,
            'description': 'Annual report - successfully processed and renamed'
        }
    ]

    print(f"Simulating processing of {len(demo_documents)} documents...")
    print()

    for i, doc in enumerate(demo_documents, 1):
        print(f"[{i}/{len(demo_documents)}] Processing Document ID {doc['document_id']}...")
        print(f"  Description: {doc['description']}")
        print(f"  Quality: {doc['quality'] if doc['quality'] else 'N/A'}")
        print(f"  Consensus: {'Yes' if doc['consensus'] else 'No'}")
        print(f"  New Title: {doc['title'] if doc['title'] else 'N/A'}")
        print(f"  Error: {doc['error'] if doc['error'] else 'None'}")
        print(f"  Processing Time: {doc['time']:.2f}s")

        # Save checkpoint
        pt.save_checkpoint(
            document_id=doc['document_id'],
            quality_response=doc['quality'],
            consensus_reached=doc['consensus'],
            new_title=doc['title'],
            error=doc['error'],
            processing_time=doc['time']
        )

        print(f"  ✅ Checkpoint saved")
        print()

    print("=" * 80)
    print("✅ Demo state created successfully!")
    print("=" * 80)
    print()

    return state_file

def show_statistics(state_file):
    """Display statistics about the demo state."""
    print("=" * 80)
    print("STATE FILE STATISTICS")
    print("=" * 80)
    print()

    with open(state_file, 'r') as f:
        state = json.load(f)

    documents = state['documents']

    print(f"📁 State File: {state_file}")
    print(f"📅 Created: {state['created_at']}")
    print(f"🔄 Last Updated: {state['last_updated']}")
    print(f"📄 Total Documents: {len(documents)}")
    print()

    # Calculate statistics
    total_processed = len(documents)
    consensus_count = sum(1 for doc in documents if doc.get('consensus_reached'))
    error_count = sum(1 for doc in documents if doc.get('error'))
    total_time = sum(doc.get('processing_time', 0) for doc in documents)

    print("📊 PROCESSING STATISTICS:")
    print(f"  Total Processed: {total_processed}")
    print(f"  Successful (Consensus): {consensus_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total Processing Time: {total_time:.2f} seconds")
    print(f"  Average Time per Document: {total_time/total_processed:.2f} seconds")
    print()

    # Show document list
    print("📋 PROCESSED DOCUMENTS:")
    for doc in documents:
        status = "✅ Success" if not doc.get('error') else "❌ Error"
        quality = doc.get('quality_response', 'N/A')
        title = doc.get('new_title', 'N/A')
        print(f"  {status} | ID {doc['document_id']} | {quality} | {title}")

    print()
    print("=" * 80)
    print()

def run_show_progress_demo(state_file):
    """Run the --show-progress command and display output."""
    print("=" * 80)
    print("RUNNING: python main.py --show-progress")
    print("=" * 80)
    print()

    # Set environment variable to use demo state file
    env = os.environ.copy()
    env['PROGRESS_STATE_FILE'] = state_file

    # Run the command
    result = subprocess.run(
        [sys.executable, 'main.py', '--show-progress'],
        capture_output=False,  # Show output directly
        env=env
    )

    print()

def cleanup(state_file):
    """Clean up demo files."""
    print("=" * 80)
    print("Cleaning up demo files...")
    print("=" * 80)

    if os.path.exists(state_file):
        os.remove(state_file)
        print(f"✅ Removed {state_file}")

    print()

def main():
    """Main demo function."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "DEMO: --show-progress FUNCTIONALITY" + " " * 24 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    try:
        # Step 1: Create demo state
        state_file = create_demo_state()

        # Step 2: Show state statistics
        show_statistics(state_file)

        # Step 3: Run --show-progress command
        input("Press Enter to see the --show-progress output...")
        print()
        run_show_progress_demo(state_file)

        # Step 4: Explanation
        print("=" * 80)
        print("WHAT YOU SEE ABOVE:")
        print("=" * 80)
        print()
        print("The --show-progress command displays:")
        print("  1. 📊 Total Documents Processed - Count of all processed documents")
        print("  2. ✅ Consensus Reached - Number of documents with successful consensus")
        print("  3. ❌ Errors - Number of documents that had errors")
        print("  4. ⏱️  Total Processing Time - Cumulative time for all documents")
        print("  5. 📅 Timestamps - When state was created and last updated")
        print("  6. 📋 Recent Documents - Last 5 processed documents with status icons")
        print()
        print("Status Icons:")
        print("  ✅ = Successfully processed")
        print("  ❌ = Error during processing")
        print()
        print("=" * 80)
        print()

        # Step 5: Cleanup
        cleanup_response = input("Clean up demo files? (y/n): ").strip().lower()
        if cleanup_response in ['y', 'yes']:
            cleanup(state_file)
        else:
            print(f"Demo state file kept at: {state_file}")
            print()

        print("=" * 80)
        print("✅ DEMO COMPLETED")
        print("=" * 80)
        print()

    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
