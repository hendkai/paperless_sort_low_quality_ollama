#!/usr/bin/env python3
"""
Test script to verify progress state saving functionality.

This script simulates document processing to test the ProgressTracker
without requiring external services (Paperless-ngx and Ollama).
"""

import json
import os
import time
from datetime import datetime
from progress_tracker import ProgressTracker

def test_basic_progress_state_saving():
    """Test that progress state is saved correctly after document processing."""

    print("=" * 80)
    print("TEST: Basic Progress State Saving")
    print("=" * 80)

    # Use a test state file
    test_state_file = "test_progress_state.json"

    # Clean up any existing test file
    if os.path.exists(test_state_file):
        os.remove(test_state_file)
        print(f"✓ Cleaned up existing test file: {test_state_file}")

    # Initialize ProgressTracker
    print(f"\n1. Initializing ProgressTracker with state file: {test_state_file}")
    tracker = ProgressTracker(test_state_file)
    print("   ✓ ProgressTracker initialized")

    # State file is created when first checkpoint is saved
    print(f"\n2. State file will be created when first checkpoint is saved")

    # Simulate processing 3 documents (as specified in MAX_DOCUMENTS=3)
    print(f"\n3. Simulating processing of 3 documents...")

    test_documents = [
        {
            'id': 101,
            'quality': 'high quality',
            'consensus': True,
            'title': 'Invoice_2024_001.pdf',
            'error': None
        },
        {
            'id': 102,
            'quality': 'low quality',
            'consensus': True,
            'title': None,
            'error': None
        },
        {
            'id': 103,
            'quality': 'high quality',
            'consensus': True,
            'title': 'Contract_Services_2024.pdf',
            'error': None
        }
    ]

    for i, doc in enumerate(test_documents, 1):
        print(f"\n   Processing document {i}/3 (ID: {doc['id']})...")
        time.sleep(0.1)  # Simulate processing time

        # Save checkpoint
        tracker.save_checkpoint(
            document_id=doc['id'],
            quality_response=doc['quality'],
            consensus_reached=doc['consensus'],
            new_title=doc['title'],
            error=doc['error'],
            processing_time=0.1 + (i * 0.05)
        )
        print(f"   ✓ Checkpoint saved for document ID {doc['id']}")

    # Verify state file contains processed document data
    print(f"\n4. Verifying state file contents...")
    try:
        with open(test_state_file, 'r') as f:
            state_data = json.load(f)

        print(f"   ✓ State file is valid JSON")

        # Check required fields
        required_fields = ['created_at', 'last_updated', 'documents']
        for field in required_fields:
            if field in state_data:
                print(f"   ✓ Field '{field}' present")
            else:
                print(f"   ✗ FAILED: Field '{field}' missing")
                return False

        # Check documents
        documents = state_data.get('documents', [])
        if len(documents) == 3:
            print(f"   ✓ Correct number of documents processed: {len(documents)}")
        else:
            print(f"   ✗ FAILED: Expected 3 documents, found {len(documents)}")
            return False

        # Verify timestamps and processing results
        print(f"\n5. Verifying timestamps and processing results...")

        for i, doc in enumerate(documents, 1):
            print(f"\n   Document {i} (ID: {doc['document_id']}):")

            # Check required document fields
            doc_fields = ['document_id', 'quality_response', 'consensus_reached',
                         'new_title', 'error', 'processing_time', 'processed_at']

            all_fields_present = True
            for field in doc_fields:
                if field in doc:
                    status = "✓"
                else:
                    status = "✗"
                    all_fields_present = False
                print(f"      {status} {field}: {doc.get(field, 'MISSING')}")

            if not all_fields_present:
                print(f"   ✗ FAILED: Some fields missing from document entry")
                return False

            # Verify timestamp format
            try:
                timestamp = datetime.fromisoformat(doc['processed_at'])
                print(f"      ✓ Timestamp is valid ISO format: {timestamp}")
            except ValueError as e:
                print(f"      ✗ FAILED: Invalid timestamp format: {e}")
                return False

            # Verify processing time is a number
            if isinstance(doc['processing_time'], (int, float)):
                print(f"      ✓ Processing time is numeric: {doc['processing_time']:.3f}s")
            else:
                print(f"      ✗ FAILED: Processing time is not numeric")
                return False

        # Test progress summary
        print(f"\n6. Testing progress summary...")
        summary = tracker.get_progress_summary()

        print(f"   Total processed: {summary['total_processed']}")
        print(f"   Consensus reached: {summary['consensus_count']}")
        print(f"   Error count: {summary['error_count']}")
        print(f"   Total processing time: {summary['total_processing_time']:.3f}s")
        print(f"   Created at: {summary['created_at']}")
        print(f"   Last updated: {summary['last_updated']}")

        if summary['total_processed'] == 3:
            print(f"   ✓ Progress summary correct")
        else:
            print(f"   ✗ FAILED: Expected 3 processed documents in summary")
            return False

    except json.JSONDecodeError as e:
        print(f"   ✗ FAILED: Invalid JSON in state file: {e}")
        return False
    except Exception as e:
        print(f"   ✗ FAILED: Error reading state file: {e}")
        return False

    # Test is_processed functionality
    print(f"\n7. Testing is_processed() method...")
    if tracker.is_processed(101):
        print(f"   ✓ Document ID 101 correctly identified as processed")
    else:
        print(f"   ✗ FAILED: Document ID 101 should be processed")
        return False

    if not tracker.is_processed(999):
        print(f"   ✓ Document ID 999 correctly identified as NOT processed")
    else:
        print(f"   ✗ FAILED: Document ID 999 should not be processed")
        return False

    print(f"\n" + "=" * 80)
    print(f"✓ ALL TESTS PASSED")
    print(f"=" * 80)
    print(f"\nSummary:")
    print(f"  - Progress state file created successfully")
    print(f"  - Processed document data saved correctly")
    print(f"  - Timestamps recorded in valid ISO format")
    print(f"  - Processing results (quality, consensus, errors) recorded")
    print(f"  - Processing times tracked")
    print(f"  - Progress summary generation works")
    print(f"  - is_processed() method works correctly")

    # Clean up test file
    os.remove(test_state_file)
    print(f"\n✓ Test file cleaned up: {test_state_file}")

    return True

if __name__ == "__main__":
    success = test_basic_progress_state_saving()
    exit(0 if success else 1)
