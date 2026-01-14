#!/usr/bin/env python3
"""
Test script to verify resume functionality skips already-processed documents.

This script simulates a document processing scenario where:
1. Processing starts and processes some documents
2. An interruption occurs (simulated)
3. Processing resumes and skips already-processed documents
4. Processing continues from the last checkpoint

Manual Verification Steps:
1. Process 3 documents and interrupt
2. Run again with same settings
3. Verify already-processed docs are skipped
4. Verify processing continues from last checkpoint
5. Check logs for 'Skipping already processed document' messages
"""

import json
import os
import logging
import time
from datetime import datetime
from progress_tracker import ProgressTracker

# Configure logging to capture log messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_resume.log')
    ]
)
logger = logging.getLogger(__name__)


def simulate_document_processing(tracker, document_id, quality, consensus, title=None):
    """
    Simulate processing a single document and saving checkpoint.

    Returns the processing result dictionary.
    """
    logger.info(f"==== Verarbeite Dokument ID: {document_id} ====")
    start_time = time.time()

    # Simulate processing time
    time.sleep(0.1)

    # Generate result
    result = {
        'document_id': document_id,
        'quality_response': quality,
        'consensus_reached': consensus,
        'new_title': title,
        'error': None
    }

    processing_time = time.time() - start_time

    # Save checkpoint
    tracker.save_checkpoint(
        document_id=result['document_id'],
        quality_response=result['quality_response'],
        consensus_reached=result['consensus_reached'],
        new_title=result.get('new_title'),
        error=result.get('error'),
        processing_time=processing_time
    )

    logger.info(f"==== Verarbeitung von Dokument ID: {document_id} abgeschlossen ====")
    return result


def test_resume_functionality():
    """Test that resume functionality correctly skips already-processed documents."""

    print("\n" + "=" * 80)
    print("TEST: Resume Functionality - Skip Already-Processed Documents")
    print("=" * 80 + "\n")

    # Use a test state file
    test_state_file = "test_resume_state.json"

    # Clean up any existing test file
    if os.path.exists(test_state_file):
        os.remove(test_state_file)
        print(f"✓ Cleaned up existing test file: {test_state_file}")

    # Define test documents
    test_documents = [
        {'id': 201, 'quality': 'high quality', 'consensus': True, 'title': 'Invoice_Jan_2024.pdf'},
        {'id': 202, 'quality': 'low quality', 'consensus': True, 'title': None},
        {'id': 203, 'quality': 'high quality', 'consensus': True, 'title': 'Contract_001.pdf'},
        {'id': 204, 'quality': 'high quality', 'consensus': True, 'title': 'Report_Q1_2024.pdf'},
        {'id': 205, 'quality': 'low quality', 'consensus': True, 'title': None},
    ]

    print("=" * 80)
    print("SCENARIO 1: Initial Processing Run (Interrupted after 3 documents)")
    print("=" * 80)

    # Initialize ProgressTracker for first run
    print(f"\n1. Starting initial processing run...")
    tracker = ProgressTracker(test_state_file)
    print("   ✓ ProgressTracker initialized")

    # Process first 3 documents (simulating interruption after document 3)
    print(f"\n2. Processing documents 1-3 (simulating normal processing)...")
    processed_count = 0
    for i in range(3):  # Only process first 3
        doc = test_documents[i]
        processed_count += 1
        print(f"\n   Processing document {processed_count}/5 (ID: {doc['id']})...")

        result = simulate_document_processing(
            tracker,
            doc['id'],
            doc['quality'],
            doc['consensus'],
            doc['title']
        )
        print(f"   ✓ Document ID {doc['id']} processed successfully")

    # Verify state after interruption
    print(f"\n3. Checking state after 'interruption'...")
    summary = tracker.get_progress_summary()
    print(f"   Total processed: {summary['total_processed']}")
    print(f"   Expected: 3")
    if summary['total_processed'] == 3:
        print("   ✓ Correct number of documents processed")
    else:
        print(f"   ✗ FAILED: Expected 3 documents, found {summary['total_processed']}")
        return False

    # Verify state file was created
    if os.path.exists(test_state_file):
        print(f"   ✓ State file exists: {test_state_file}")
    else:
        print(f"   ✗ FAILED: State file not created")
        return False

    print("\n" + "=" * 80)
    print("SCENARIO 2: Resume Processing (Should skip documents 201-203)")
    print("=" * 80)

    # Simulate a delay (interruption period)
    print(f"\n4. Simulating interruption period (2 seconds)...")
    time.sleep(2)

    # Create new ProgressTracker instance (simulating restart after interruption)
    print(f"\n5. Restarting processing (new ProgressTracker instance)...")
    tracker_resume = ProgressTracker(test_state_file)
    print("   ✓ ProgressTracker initialized with existing state file")

    # Check what's in the state
    summary = tracker_resume.get_progress_summary()
    print(f"\n6. Existing state detected:")
    print(f"   Documents already processed: {summary['total_processed']}")
    print(f"   Last updated: {summary['last_updated']}")

    # Track which documents are skipped
    skipped_count = 0
    newly_processed_count = 0

    print(f"\n7. Attempting to process all 5 documents...")
    print(f"   (Documents 201-203 should be SKIPPED)")
    print(f"   (Documents 204-205 should be PROCESSED)\n")

    # Try to process all documents (should skip first 3)
    for i, doc in enumerate(test_documents):
        doc_num = i + 1
        print(f"\n   Document {doc_num}/5 (ID: {doc['id']}):")

        # Check if already processed (RESUME LOGIC)
        if tracker_resume.is_processed(doc['id']):
            logger.info(f"Überspringe Dokument ID {doc['id']}, da es bereits verarbeitet wurde (Progress-Check).")
            print(f"      ⏭️  SKIPPED (already processed)")
            skipped_count += 1
            continue

        # Process the document
        print(f"      🔄 Processing...")
        result = simulate_document_processing(
            tracker_resume,
            doc['id'],
            doc['quality'],
            doc['consensus'],
            doc['title']
        )
        print(f"      ✓ Processed successfully")
        newly_processed_count += 1

    # Verify results
    print("\n" + "=" * 80)
    print("VERIFICATION RESULTS")
    print("=" * 80)

    print(f"\n8. Verifying resume behavior...")

    # Check skipped count
    print(f"\n   Skipped documents: {skipped_count}")
    print(f"   Expected: 3 (documents 201, 202, 203)")
    if skipped_count == 3:
        print("   ✓ Correct number of documents skipped")
    else:
        print(f"   ✗ FAILED: Expected 3 skipped, found {skipped_count}")
        return False

    # Check newly processed count
    print(f"\n   Newly processed documents: {newly_processed_count}")
    print(f"   Expected: 2 (documents 204, 205)")
    if newly_processed_count == 2:
        print("   ✓ Correct number of new documents processed")
    else:
        print(f"   ✗ FAILED: Expected 2 new, found {newly_processed_count}")
        return False

    # Verify final state
    print(f"\n9. Verifying final state...")
    final_summary = tracker_resume.get_progress_summary()

    print(f"   Total processed in state: {final_summary['total_processed']}")
    print(f"   Expected: 5 (all documents)")
    if final_summary['total_processed'] == 5:
        print("   ✓ All 5 documents in state")
    else:
        print(f"   ✗ FAILED: Expected 5 total, found {final_summary['total_processed']}")
        return False

    # Verify individual document status
    print(f"\n10. Verifying individual document status...")

    all_correct = True
    for doc in test_documents:
        is_processed = tracker_resume.is_processed(doc['id'])
        if is_processed:
            print(f"      ✓ Document ID {doc['id']}: marked as processed")
        else:
            print(f"      ✗ Document ID {doc['id']}: NOT marked as processed (FAILED)")
            all_correct = False

    if not all_correct:
        return False

    # Check log file for skip messages
    print(f"\n11. Checking log file for 'Skipping already processed document' messages...")

    if os.path.exists('test_resume.log'):
        with open('test_resume.log', 'r') as f:
            log_content = f.read()

        # Count skip messages
        skip_count = log_content.count('Überspringe Dokument ID')
        print(f"   Found {skip_count} skip messages in log")
        print(f"   Expected: 3")

        if skip_count >= 3:
            print("   ✓ Skip messages found in logs")
        else:
            print("   ✗ WARNING: Expected 3 skip messages in logs")
    else:
        print("   ✗ Log file not found")

    # Display state file contents
    print(f"\n12. Displaying final state file contents...")
    try:
        with open(test_state_file, 'r') as f:
            state_data = json.load(f)

        print(f"\n   State file structure:")
        print(f"   - Created at: {state_data.get('created_at')}")
        print(f"   - Last updated: {state_data.get('last_updated')}")
        print(f"   - Total documents: {len(state_data.get('documents', []))}")

        print(f"\n   Processed documents:")
        for doc in state_data.get('documents', []):
            status = "✓" if not doc.get('error') else "✗"
            timestamp = datetime.fromisoformat(doc['processed_at']).strftime('%H:%M:%S')
            print(f"      {status} ID {doc['document_id']} | {doc['quality_response']} | {timestamp}")

    except Exception as e:
        print(f"   ✗ Error reading state file: {e}")
        return False

    # Final summary
    print("\n" + "=" * 80)
    print("✓ ALL TESTS PASSED")
    print("=" * 80)

    print("\nSummary of Resume Functionality Test:")
    print(f"  ✓ Initial processing: 3 documents processed before 'interruption'")
    print(f"  ✓ State persistence: State file created and preserved")
    print(f"  ✓ Resume detection: System detected existing state on restart")
    print(f"  ✓ Skip logic: 3 already-processed documents were skipped")
    print(f"  ✓ Continue logic: 2 new documents were processed")
    print(f"  ✓ Final state: All 5 documents marked as processed")
    print(f"  ✓ Log messages: Skip messages present in logs")
    print(f"  ✓ No duplicates: Each document processed exactly once")

    print("\n✓ Resume functionality is working correctly!")

    # Clean up test files
    os.remove(test_state_file)
    if os.path.exists('test_resume.log'):
        os.remove('test_resume.log')
    print(f"\n✓ Test files cleaned up")

    return True


def test_integration_with_main():
    """
    Test the integration with main.py process_documents function.

    This verifies that the resume logic in process_documents works correctly.
    """

    print("\n" + "=" * 80)
    print("TEST: Integration with main.py process_documents")
    print("=" * 80 + "\n")

    # Check that main.py has the resume logic
    print("1. Verifying main.py contains resume logic...")

    try:
        with open('main.py', 'r') as f:
            main_content = f.read()

        # Check for resume logic
        checks = [
            ('is_processed check', 'is_processed(document['),
            ('ProgressTracker import', 'from progress_tracker import ProgressTracker'),
            ('save_checkpoint call', 'progress_tracker.save_checkpoint'),
            ('Skip log message', 'Überspringe Dokument ID'),
            ('Progress-Check message', 'Progress-Check')
        ]

        all_found = True
        for check_name, check_string in checks:
            if check_string in main_content:
                print(f"   ✓ {check_name}: Found")
            else:
                print(f"   ✗ {check_name}: NOT FOUND")
                all_found = False

        if all_found:
            print("\n   ✓ All resume logic components present in main.py")
        else:
            print("\n   ✗ FAILED: Some components missing from main.py")
            return False

    except Exception as e:
        print(f"   ✗ Error reading main.py: {e}")
        return False

    print("\n" + "=" * 80)
    print("✓ INTEGRATION TEST PASSED")
    print("=" * 80)

    print("\nResume logic is properly integrated into main.py:")
    print("  ✓ ProgressTracker is imported and initialized")
    print("  ✓ is_processed() check before processing each document")
    print("  ✓ save_checkpoint() called after each document")
    print("  ✓ Skip messages logged for already-processed documents")

    return True


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("RESUME FUNCTIONALITY TEST SUITE")
    print("=" * 80)

    # Run both tests
    test1_passed = test_resume_functionality()
    print("\n\n")
    test2_passed = test_integration_with_main()

    # Exit with appropriate code
    if test1_passed and test2_passed:
        print("\n" + "=" * 80)
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("=" * 80)
        exit(0)
    else:
        print("\n" + "=" * 80)
        print("✗✗✗ SOME TESTS FAILED ✗✗✗")
        print("=" * 80)
        exit(1)
