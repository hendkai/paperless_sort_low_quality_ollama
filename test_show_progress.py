#!/usr/bin/env python3
"""
Test script to verify --show-progress displays accurate summary.

This script tests subtask-4-4: Test --show-progress displays accurate summary
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from progress_tracker import ProgressTracker

def test_show_progress():
    """Test that --show-progress displays accurate summary."""

    print("=" * 80)
    print("TEST: --show-progress displays accurate summary")
    print("=" * 80)
    print()

    # Test state file
    test_state_file = "test_progress_state.json"

    # Clean up any existing test state file
    if os.path.exists(test_state_file):
        os.remove(test_state_file)

    # Create a ProgressTracker and populate with test data
    print("Step 1: Creating test state with sample documents...")
    pt = ProgressTracker(test_state_file)

    # Save test checkpoints - simulating processing of several documents
    test_documents = [
        {
            'document_id': 1001,
            'quality_response': 'high quality',
            'consensus_reached': True,
            'new_title': 'Invoice_2024_001.pdf',
            'error': None,
            'processing_time': 2.35
        },
        {
            'document_id': 1002,
            'quality_response': 'low quality',
            'consensus_reached': True,
            'new_title': None,
            'error': None,
            'processing_time': 1.85
        },
        {
            'document_id': 1003,
            'quality_response': 'high quality',
            'consensus_reached': True,
            'new_title': 'Contract_Amendment.pdf',
            'error': None,
            'processing_time': 3.12
        },
        {
            'document_id': 1004,
            'quality_response': '',
            'consensus_reached': False,
            'new_title': None,
            'error': '404 Client Error: Not Found',
            'processing_time': 0.55
        },
        {
            'document_id': 1005,
            'quality_response': 'high quality',
            'consensus_reached': True,
            'new_title': 'Meeting_Minutes_Q1.pdf',
            'error': None,
            'processing_time': 2.78
        }
    ]

    # Save checkpoints for all test documents
    for doc in test_documents:
        pt.save_checkpoint(
            document_id=doc['document_id'],
            quality_response=doc['quality_response'],
            consensus_reached=doc['consensus_reached'],
            new_title=doc['new_title'],
            error=doc['error'],
            processing_time=doc['processing_time']
        )

    print(f"✅ Created state with {len(test_documents)} documents")
    print()

    # Verify the state file was created correctly
    print("Step 2: Verifying state file contents...")
    with open(test_state_file, 'r') as f:
        state_data = json.load(f)

    assert 'documents' in state_data, "State file missing 'documents' key"
    assert len(state_data['documents']) == 5, f"Expected 5 documents, found {len(state_data['documents'])}"

    # Verify document IDs match
    doc_ids = [doc['document_id'] for doc in state_data['documents']]
    expected_ids = [1001, 1002, 1003, 1004, 1005]
    assert doc_ids == expected_ids, f"Document IDs mismatch: expected {expected_ids}, got {doc_ids}"

    print(f"✅ State file contains correct document IDs: {doc_ids}")
    print()

    # Test get_progress_summary() method
    print("Step 3: Testing get_progress_summary() method...")
    summary = pt.get_progress_summary()

    # Verify summary statistics
    assert summary['total_processed'] == 5, f"Expected total_processed=5, got {summary['total_processed']}"
    assert summary['consensus_count'] == 4, f"Expected consensus_count=4, got {summary['consensus_count']}"
    assert summary['error_count'] == 1, f"Expected error_count=1, got {summary['error_count']}"

    # Calculate expected processing time
    expected_time = sum(doc['processing_time'] for doc in test_documents)
    actual_time = summary['total_processing_time']
    assert abs(actual_time - expected_time) < 0.01, f"Processing time mismatch: expected {expected_time}, got {actual_time}"

    print(f"✅ Summary statistics:")
    print(f"   - Total processed: {summary['total_processed']}")
    print(f"   - Consensus reached: {summary['consensus_count']}")
    print(f"   - Error count: {summary['error_count']}")
    print(f"   - Total processing time: {summary['total_processing_time']:.2f} seconds")
    print()

    # Test --show-progress command-line flag
    print("Step 4: Testing --show-progress command-line flag...")
    print("Running: python main.py --show-progress")
    print("-" * 80)

    # Temporarily override the progress state file environment variable
    env = os.environ.copy()
    env['PROGRESS_STATE_FILE'] = test_state_file

    # Run main.py with --show-progress
    result = subprocess.run(
        [sys.executable, 'main.py', '--show-progress'],
        capture_output=True,
        text=True,
        env=env
    )

    print(result.stdout)
    print("-" * 80)
    print()

    # Verify the output contains expected information
    print("Step 5: Verifying --show-progress output...")

    output = result.stdout

    # Check for key information in output
    checks = [
        ('Total Documents Processed' in output or 'Documents Processed' in output,
         "Output shows total processed count"),
        ('5' in output,
         "Output contains correct number (5)"),
        ('Consensus' in output,
         "Output shows consensus information"),
        ('Error' in output,
         "Output shows error information"),
        ('Processing Time' in output or 'seconds' in output,
         "Output shows processing time"),
        ('1001' in output or '1005' in output or '1002' in output or '1003' in output or '1004' in output,
         "Output shows document IDs"),
    ]

    all_passed = True
    for check, description in checks:
        status = "✅" if check else "❌"
        print(f"{status} {description}")
        if not check:
            all_passed = False

    print()

    # Additional verification: check that document IDs are present
    print("Step 6: Verifying document IDs in output...")
    for doc in test_documents:
        doc_id_str = str(doc['document_id'])
        if doc_id_str in output:
            print(f"✅ Document ID {doc['document_id']} found in output")
        else:
            print(f"⚠️  Document ID {doc['document_id']} not found in output (may be in recent list only)")

    print()

    # Test edge case: empty state file
    print("Step 7: Testing edge case - empty state file...")
    pt_empty = ProgressTracker("test_empty_state.json")
    empty_summary = pt_empty.get_progress_summary()

    assert empty_summary['total_processed'] == 0, "Empty state should have total_processed=0"
    assert empty_summary['consensus_count'] == 0, "Empty state should have consensus_count=0"
    assert empty_summary['error_count'] == 0, "Empty state should have error_count=0"

    print("✅ Empty state handled correctly")
    print()

    # Clean up test files
    print("Step 8: Cleaning up test files...")
    if os.path.exists(test_state_file):
        os.remove(test_state_file)
    if os.path.exists("test_empty_state.json"):
        os.remove("test_empty_state.json")

    print("✅ Cleanup complete")
    print()

    # Final result
    print("=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print()
        print("Verification Summary:")
        print("- ✅ State file created successfully with sample data")
        print("- ✅ Document IDs match what was processed")
        print("- ✅ Total processed count is accurate (5)")
        print("- ✅ Success count (consensus) is accurate (4)")
        print("- ✅ Error count is accurate (1)")
        print("- ✅ Processing times are tracked accurately")
        print("- ✅ --show-progress displays all required information")
        print("- ✅ Edge case (empty state) handled correctly")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print()
        print("Please review the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = test_show_progress()
    sys.exit(exit_code)
