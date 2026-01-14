#!/usr/bin/env python3
"""
Test error handling and recovery for corrupted state file.

This script tests various scenarios of corrupted progress_state.json files
to verify that the application handles them gracefully.
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path


def create_test_environment():
    """Create a temporary directory for testing."""
    test_dir = tempfile.mkdtemp(prefix="progress_test_")
    return test_dir


def cleanup_test_environment(test_dir):
    """Clean up the temporary test directory."""
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print(f"✅ Cleaned up test directory: {test_dir}")


def test_invalid_json():
    """Test recovery from completely invalid JSON."""
    print("\n" + "="*60)
    print("TEST 1: Invalid JSON (gibberish content)")
    print("="*60)

    test_dir = create_test_environment()
    state_file = os.path.join(test_dir, "test_state.json")

    try:
        # Create invalid JSON
        with open(state_file, 'w') as f:
            f.write("This is not valid JSON at all! {broken content")

        print(f"Created corrupted state file: {state_file}")
        print(f"Content: 'This is not valid JSON at all! {{broken content'")

        # Try to load with ProgressTracker
        sys.path.insert(0, os.getcwd())
        from progress_tracker import ProgressTracker

        pt = ProgressTracker(state_file)

        # Verify recovery
        assert 'documents' in pt.state, "State should have documents key"
        assert len(pt.state['documents']) == 0, "Documents should be empty after recovery"
        assert 'created_at' in pt.state, "State should have created_at timestamp"

        print("✅ PASS: Application recovered from invalid JSON")
        print(f"   New state created with {len(pt.state['documents'])} documents")

        # Verify a new valid file was created
        with open(state_file, 'r') as f:
            new_content = f.read()
            json.loads(new_content)  # Should be valid now
        print("✅ PASS: New state file contains valid JSON")

    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False
    finally:
        cleanup_test_environment(test_dir)

    return True


def test_truncated_json():
    """Test recovery from truncated JSON file."""
    print("\n" + "="*60)
    print("TEST 2: Truncated JSON (incomplete file)")
    print("="*60)

    test_dir = create_test_environment()
    state_file = os.path.join(test_dir, "test_state.json")

    try:
        # Create truncated JSON
        valid_state = {
            'created_at': '2024-01-01T00:00:00',
            'last_updated': '2024-01-01T00:00:00',
            'documents': [
                {'document_id': 1, 'quality_response': 'high quality'}
            ]
        }
        json_content = json.dumps(valid_state, indent=2)
        truncated_content = json_content[:len(json_content)//2]  # Cut in half

        with open(state_file, 'w') as f:
            f.write(truncated_content)

        print(f"Created truncated state file: {state_file}")
        print(f"Content (first 100 chars): {truncated_content[:100]}...")

        # Try to load with ProgressTracker
        from progress_tracker import ProgressTracker
        pt = ProgressTracker(state_file)

        # Verify recovery
        assert 'documents' in pt.state, "State should have documents key"
        assert len(pt.state['documents']) == 0, "Documents should be empty after recovery"

        print("✅ PASS: Application recovered from truncated JSON")
        print(f"   New state created with {len(pt.state['documents'])} documents")

    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False
    finally:
        cleanup_test_environment(test_dir)

    return True


def test_malformed_structure():
    """Test recovery from JSON with wrong structure."""
    print("\n" + "="*60)
    print("TEST 3: Malformed JSON structure (wrong keys)")
    print("="*60)

    test_dir = create_test_environment()
    state_file = os.path.join(test_dir, "test_state.json")

    try:
        # Create valid JSON but wrong structure
        wrong_structure = {
            'wrong_key': 'wrong_value',
            'data': [1, 2, 3],
            'invalid': True
        }

        with open(state_file, 'w') as f:
            json.dump(wrong_structure, f, indent=2)

        print(f"Created state file with wrong structure: {state_file}")

        # Try to load with ProgressTracker
        from progress_tracker import ProgressTracker
        pt = ProgressTracker(state_file)

        # Verify recovery - should create new proper structure
        assert 'documents' in pt.state, "State should have documents key"
        assert 'created_at' in pt.state, "State should have created_at"
        assert 'last_updated' in pt.state, "State should have last_updated"

        print("✅ PASS: Application recovered from malformed structure")
        print(f"   New proper state structure created")

    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False
    finally:
        cleanup_test_environment(test_dir)

    return True


def test_empty_file():
    """Test recovery from empty file."""
    print("\n" + "="*60)
    print("TEST 4: Empty file")
    print("="*60)

    test_dir = create_test_environment()
    state_file = os.path.join(test_dir, "test_state.json")

    try:
        # Create empty file
        with open(state_file, 'w') as f:
            f.write("")

        print(f"Created empty state file: {state_file}")

        # Try to load with ProgressTracker
        from progress_tracker import ProgressTracker
        pt = ProgressTracker(state_file)

        # Verify recovery
        assert 'documents' in pt.state, "State should have documents key"
        assert len(pt.state['documents']) == 0, "Documents should be empty"

        print("✅ PASS: Application recovered from empty file")

    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False
    finally:
        cleanup_test_environment(test_dir)

    return True


def test_main_py_integration():
    """Test that main.py can handle corrupted state file on startup."""
    print("\n" + "="*60)
    print("TEST 5: Integration test with main.py startup")
    print("="*60)

    test_dir = create_test_environment()
    original_state_file = os.path.join(os.getcwd(), "progress_state.json")
    backup_state_file = None

    try:
        # Backup existing state file if it exists
        if os.path.exists(original_state_file):
            backup_state_file = original_state_file + ".backup"
            shutil.copy2(original_state_file, backup_state_file)
            print(f"Backed up existing state file to: {backup_state_file}")

        # Create corrupted state file
        with open(original_state_file, 'w') as f:
            f.write("{corrupted json content broken syntax")

        print(f"Created corrupted state file: {original_state_file}")

        # Try importing main (which initializes ProgressTracker)
        import importlib
        import main

        # Reload to trigger initialization with corrupted file
        importlib.reload(main)

        print("✅ PASS: main.py loaded successfully despite corrupted state file")

        # Verify a new valid state file was created
        assert os.path.exists(original_state_file), "State file should exist"
        with open(original_state_file, 'r') as f:
            json.load(f)  # Should be valid JSON
        print("✅ PASS: New valid state file was created")

    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore backup if it existed
        if backup_state_file and os.path.exists(backup_state_file):
            shutil.copy2(backup_state_file, original_state_file)
            os.remove(backup_state_file)
            print(f"✅ Restored original state file from backup")
        elif os.path.exists(original_state_file):
            # Remove the test state file if no backup existed
            try:
                os.remove(original_state_file)
                print(f"✅ Removed test state file")
            except:
                pass

        cleanup_test_environment(test_dir)

    return True


def print_summary(results):
    """Print test summary."""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for r in results if r)
    total = len(results)

    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"Test {i}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Error handling works correctly.")
        return True
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    print("="*60)
    print("PROGRESS TRACKER - CORRUPTED STATE ERROR HANDLING TESTS")
    print("="*60)
    print("\nThis test suite verifies that the application handles")
    print("corrupted progress_state.json files gracefully.\n")

    results = []

    # Run all tests
    results.append(test_invalid_json())
    results.append(test_truncated_json())
    results.append(test_malformed_structure())
    results.append(test_empty_file())
    results.append(test_main_py_integration())

    # Print summary
    all_passed = print_summary(results)

    sys.exit(0 if all_passed else 1)
