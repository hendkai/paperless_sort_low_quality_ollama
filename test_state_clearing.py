#!/usr/bin/env python3
"""
Test script to verify state clearing and fresh start functionality.

This script simulates a document processing scenario where:
1. Some documents are processed to create state
2. State is cleared using --clear-state flag
3. Processing starts fresh - all documents are processed again
4. No documents are skipped

Manual Verification Steps:
1. Process some documents to create state
2. Run main.py --clear-state
3. Verify progress_state.json is empty/deleted
4. Run processing again - all documents should be processed
5. Verify no documents are skipped
"""

import json
import os
import logging
import time
import subprocess
import sys
from datetime import datetime
from progress_tracker import ProgressTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_state_clearing.log')
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
    time.sleep(0.05)

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


def test_state_clearing_method():
    """Test that the ProgressTracker.clear_state() method works correctly."""

    print("\n" + "=" * 80)
    print("TEST 1: ProgressTracker.clear_state() Method")
    print("=" * 80 + "\n")

    # Use a test state file
    test_state_file = "test_clear_state.json"

    # Clean up any existing test file
    if os.path.exists(test_state_file):
        os.remove(test_state_file)
        print(f"✓ Cleaned up existing test file: {test_state_file}")

    # Define test documents
    test_documents = [
        {'id': 301, 'quality': 'high quality', 'consensus': True, 'title': 'Report_A.pdf'},
        {'id': 302, 'quality': 'low quality', 'consensus': True, 'title': None},
        {'id': 303, 'quality': 'high quality', 'consensus': True, 'title': 'Invoice_001.pdf'},
    ]

    print("\n1. Creating initial state by processing 3 documents...")
    tracker = ProgressTracker(test_state_file)
    print("   ✓ ProgressTracker initialized")

    # Process all documents
    for i, doc in enumerate(test_documents, 1):
        print(f"   Processing document {i}/3 (ID: {doc['id']})...")
        simulate_document_processing(
            tracker,
            doc['id'],
            doc['quality'],
            doc['consensus'],
            doc['title']
        )
        print(f"   ✓ Document ID {doc['id']} processed")

    # Verify state was created
    print("\n2. Verifying initial state...")
    summary = tracker.get_progress_summary()
    print(f"   Total processed: {summary['total_processed']}")
    if summary['total_processed'] == 3:
        print("   ✓ 3 documents processed")
    else:
        print(f"   ✗ FAILED: Expected 3 documents, found {summary['total_processed']}")
        return False

    if os.path.exists(test_state_file):
        print(f"   ✓ State file exists: {test_state_file}")
    else:
        print(f"   ✗ FAILED: State file not created")
        return False

    # Read state file to verify contents
    try:
        with open(test_state_file, 'r') as f:
            state_data = json.load(f)
        doc_count = len(state_data.get('documents', []))
        print(f"   Documents in state file: {doc_count}")
        if doc_count == 3:
            print("   ✓ State file contains 3 documents")
        else:
            print(f"   ✗ FAILED: Expected 3 documents in file, found {doc_count}")
            return False
    except Exception as e:
        print(f"   ✗ FAILED: Error reading state file: {e}")
        return False

    print("\n3. Clearing state using clear_state() method...")
    tracker.clear_state()
    print("   ✓ clear_state() called")

    # Verify state was cleared
    print("\n4. Verifying state was cleared...")
    summary = tracker.get_progress_summary()
    print(f"   Total processed after clear: {summary['total_processed']}")
    if summary['total_processed'] == 0:
        print("   ✓ State cleared - 0 documents in state")
    else:
        print(f"   ✗ FAILED: Expected 0 documents, found {summary['total_processed']}")
        return False

    # Verify documents are marked as not processed
    all_not_processed = True
    for doc in test_documents:
        if tracker.is_processed(doc['id']):
            print(f"   ✗ FAILED: Document ID {doc['id']} still marked as processed")
            all_not_processed = False

    if all_not_processed:
        print("   ✓ All documents now marked as NOT processed")
    else:
        return False

    # Verify state file still exists but is empty
    try:
        with open(test_state_file, 'r') as f:
            state_data = json.load(f)
        doc_count = len(state_data.get('documents', []))
        print(f"   Documents in state file after clear: {doc_count}")
        if doc_count == 0:
            print("   ✓ State file exists but has empty documents list")
        else:
            print(f"   ✗ FAILED: Expected 0 documents in file, found {doc_count}")
            return False
    except Exception as e:
        print(f"   ✗ FAILED: Error reading state file: {e}")
        return False

    print("\n5. Processing documents again after state clear...")
    processed_count = 0
    for doc in test_documents:
        # Check if already processed (should NOT be)
        if tracker.is_processed(doc['id']):
            print(f"   ✗ FAILED: Document ID {doc['id']} should NOT be marked as processed")
            return False

        # Process the document
        print(f"   Processing document ID {doc['id']}...")
        simulate_document_processing(
            tracker,
            doc['id'],
            doc['quality'],
            doc['consensus'],
            doc['title']
        )
        processed_count += 1
        print(f"   ✓ Document ID {doc['id']} processed (fresh start)")

    if processed_count == 3:
        print(f"\n   ✓ All 3 documents processed again (no skips)")
    else:
        print(f"   ✗ FAILED: Expected 3 documents processed, found {processed_count}")
        return False

    # Verify final state
    print("\n6. Verifying final state after re-processing...")
    final_summary = tracker.get_progress_summary()
    if final_summary['total_processed'] == 3:
        print("   ✓ Final state: 3 documents processed")
    else:
        print(f"   ✗ FAILED: Expected 3 documents, found {final_summary['total_processed']}")
        return False

    print("\n" + "=" * 80)
    print("✓ TEST 1 PASSED")
    print("=" * 80)

    # Clean up test file
    os.remove(test_state_file)
    print(f"\n✓ Test file cleaned up: {test_state_file}")

    return True


def test_cli_clear_state_flag():
    """Test the --clear-state command-line flag."""

    print("\n" + "=" * 80)
    print("TEST 2: --clear-state Command-Line Flag")
    print("=" * 80 + "\n")

    # Use a test state file
    test_state_file = "test_cli_clear_state.json"

    # Clean up any existing test file
    if os.path.exists(test_state_file):
        os.remove(test_state_file)
        print(f"✓ Cleaned up existing test file: {test_state_file}")

    print("\n1. Creating initial state by processing 3 documents...")
    tracker = ProgressTracker(test_state_file)
    print("   ✓ ProgressTracker initialized")

    # Process some documents
    test_documents = [
        {'id': 401, 'quality': 'high quality', 'consensus': True, 'title': 'Doc_A.pdf'},
        {'id': 402, 'quality': 'low quality', 'consensus': True, 'title': None},
        {'id': 403, 'quality': 'high quality', 'consensus': True, 'title': 'Doc_B.pdf'},
    ]

    for doc in test_documents:
        simulate_document_processing(
            tracker,
            doc['id'],
            doc['quality'],
            doc['consensus'],
            doc['title']
        )

    print(f"   ✓ 3 documents processed")

    # Verify state
    summary = tracker.get_progress_summary()
    if summary['total_processed'] == 3:
        print(f"   ✓ State created with {summary['total_processed']} documents")
    else:
        print(f"   ✗ FAILED: Expected 3 documents")
        return False

    print("\n2. Testing --clear-state flag...")
    print("   Running: python main.py --clear-state")

    # Set environment variable for test state file
    import subprocess
    env = os.environ.copy()
    env['PROGRESS_STATE_FILE'] = test_state_file

    try:
        # Run main.py with --clear-state flag
        result = subprocess.run(
            [sys.executable, 'main.py', '--clear-state'],
            capture_output=True,
            text=True,
            env=env,
            timeout=10
        )

        print(f"   Exit code: {result.returncode}")
        if result.returncode == 0:
            print("   ✓ Command executed successfully")
        else:
            print(f"   ✗ FAILED: Command returned non-zero exit code")
            print(f"   stderr: {result.stderr}")
            return False

        # Check output for success message
        if 'State cleared successfully' in result.stdout or '✅' in result.stdout:
            print("   ✓ Success message found in output")
        else:
            print("   Note: Expected success message not found in output")
            print(f"   Output: {result.stdout[:200]}")

    except subprocess.TimeoutExpired:
        print("   ✗ FAILED: Command timed out")
        return False
    except Exception as e:
        print(f"   ✗ FAILED: Error running command: {e}")
        return False

    print("\n3. Verifying state was cleared by CLI command...")
    # Create new tracker instance to check state
    tracker_after = ProgressTracker(test_state_file)
    summary_after = tracker_after.get_progress_summary()

    print(f"   Total processed after --clear-state: {summary_after['total_processed']}")
    if summary_after['total_processed'] == 0:
        print("   ✓ State cleared successfully by --clear-state flag")
    else:
        print(f"   ✗ FAILED: Expected 0 documents, found {summary_after['total_processed']}")
        return False

    # Verify all documents are now marked as not processed
    print("\n4. Verifying all documents can be processed again...")
    all_not_processed = True
    for doc in test_documents:
        if tracker_after.is_processed(doc['id']):
            print(f"   ✗ Document ID {doc['id']} still marked as processed")
            all_not_processed = False

    if all_not_processed:
        print("   ✓ All documents now marked as NOT processed")
    else:
        return False

    print("\n" + "=" * 80)
    print("✓ TEST 2 PASSED")
    print("=" * 80)

    # Clean up test file
    os.remove(test_state_file)
    print(f"\n✓ Test file cleaned up: {test_state_file}")

    return True


def test_fresh_start_functionality():
    """Test complete fresh start workflow."""

    print("\n" + "=" * 80)
    print("TEST 3: Complete Fresh Start Workflow")
    print("=" * 80 + "\n")

    # Use a test state file
    test_state_file = "test_fresh_start.json"

    # Clean up any existing test file
    if os.path.exists(test_state_file):
        os.remove(test_state_file)
        print(f"✓ Cleaned up existing test file: {test_state_file}")

    test_documents = [
        {'id': 501, 'quality': 'high quality', 'consensus': True, 'title': 'Fresh_A.pdf'},
        {'id': 502, 'quality': 'low quality', 'consensus': True, 'title': None},
        {'id': 503, 'quality': 'high quality', 'consensus': True, 'title': 'Fresh_B.pdf'},
        {'id': 504, 'quality': 'high quality', 'consensus': True, 'title': 'Fresh_C.pdf'},
    ]

    print("\n1. INITIAL PROCESSING RUN")
    print("-" * 80)

    tracker1 = ProgressTracker(test_state_file)
    print("   Starting initial processing...")

    for doc in test_documents[:2]:  # Process only first 2
        simulate_document_processing(
            tracker1,
            doc['id'],
            doc['quality'],
            doc['consensus'],
            doc['title']
        )
        print(f"   ✓ Document ID {doc['id']} processed")

    summary1 = tracker1.get_progress_summary()
    print(f"\n   Initial run complete: {summary1['total_processed']} documents processed")

    print("\n2. USER RUNS --clear-state")
    print("-" * 80)
    print("   User wants to start fresh...")
    tracker1.clear_state()
    print("   ✓ State cleared")

    print("\n3. FRESH START PROCESSING RUN")
    print("-" * 80)
    print("   Starting fresh processing...")

    # Create new tracker instance (simulating restart)
    tracker2 = ProgressTracker(test_state_file)
    processed_count = 0
    skipped_count = 0

    # Try to process all 4 documents
    for doc in test_documents:
        if tracker2.is_processed(doc['id']):
            print(f"   ⏭️  Document ID {doc['id']}: SKIPPED (should not happen)")
            skipped_count += 1
        else:
            print(f"   🔄 Document ID {doc['id']}: Processing...")
            simulate_document_processing(
                tracker2,
                doc['id'],
                doc['quality'],
                doc['consensus'],
                doc['title']
            )
            print(f"   ✓ Document ID {doc['id']} processed")
            processed_count += 1

    print("\n4. VERIFICATION")
    print("-" * 80)

    print(f"   Documents processed: {processed_count}")
    print(f"   Documents skipped: {skipped_count}")

    if processed_count == 4 and skipped_count == 0:
        print("   ✓ All 4 documents processed, none skipped")
    else:
        print(f"   ✗ FAILED: Expected 4 processed, 0 skipped")
        print(f"             Got {processed_count} processed, {skipped_count} skipped")
        return False

    # Verify final state
    final_summary = tracker2.get_progress_summary()
    if final_summary['total_processed'] == 4:
        print("   ✓ Final state: All 4 documents in state")
    else:
        print(f"   ✗ FAILED: Expected 4 documents in state, found {final_summary['total_processed']}")
        return False

    # Verify each document
    print("\n   Document status:")
    for doc in test_documents:
        is_processed = tracker2.is_processed(doc['id'])
        status = "✓" if is_processed else "✗"
        print(f"      {status} Document ID {doc['id']}: {'processed' if is_processed else 'NOT processed'}")

    print("\n" + "=" * 80)
    print("✓ TEST 3 PASSED")
    print("=" * 80)

    print("\n✓ Fresh start workflow is working correctly!")
    print("  - Initial state created with 2 documents")
    print("  - State cleared successfully")
    print("  - All 4 documents processed on fresh start (no skips)")

    # Clean up test file
    os.remove(test_state_file)
    print(f"\n✓ Test file cleaned up: {test_state_file}")

    return True


def test_integration_with_main():
    """Test integration with main.py."""

    print("\n" + "=" * 80)
    print("TEST 4: Integration with main.py")
    print("=" * 80 + "\n")

    print("1. Verifying main.py contains clear-state logic...")

    try:
        with open('main.py', 'r') as f:
            main_content = f.read()

        checks = [
            ('--clear-state argument', "'--clear-state'"),
            ('clear_state() call', 'progress_tracker.clear_state()'),
            ('Success message', 'State cleared successfully'),
        ]

        all_found = True
        for check_name, check_string in checks:
            if check_string in main_content:
                print(f"   ✓ {check_name}: Found")
            else:
                print(f"   ✗ {check_name}: NOT FOUND")
                all_found = False

        if all_found:
            print("\n   ✓ All clear-state components present in main.py")
        else:
            print("\n   ✗ FAILED: Some components missing from main.py")
            return False

    except Exception as e:
        print(f"   ✗ Error reading main.py: {e}")
        return False

    print("\n" + "=" * 80)
    print("✓ TEST 4 PASSED")
    print("=" * 80)

    return True


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("STATE CLEARING AND FRESH START TEST SUITE")
    print("=" * 80)

    # Run all tests
    test1_passed = test_state_clearing_method()
    print("\n\n")
    test2_passed = test_cli_clear_state_flag()
    print("\n\n")
    test3_passed = test_fresh_start_functionality()
    print("\n\n")
    test4_passed = test_integration_with_main()

    # Clean up log file
    if os.path.exists('test_state_clearing.log'):
        os.remove('test_state_clearing.log')

    # Exit with appropriate code
    if test1_passed and test2_passed and test3_passed and test4_passed:
        print("\n" + "=" * 80)
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("=" * 80)

        print("\nSummary of State Clearing Tests:")
        print("  ✓ ProgressTracker.clear_state() method works correctly")
        print("  ✓ --clear-state command-line flag works")
        print("  ✓ State file is cleared but not deleted")
        print("  ✓ All documents marked as NOT processed after clear")
        print("  ✓ Fresh start processes all documents (no skips)")
        print("  ✓ Integration with main.py verified")

        print("\n✓ State clearing and fresh start functionality is working correctly!")
        exit(0)
    else:
        print("\n" + "=" * 80)
        print("✗✗✗ SOME TESTS FAILED ✗✗✗")
        print("=" * 80)
        exit(1)
