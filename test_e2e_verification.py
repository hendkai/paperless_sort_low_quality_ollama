#!/usr/bin/env python3
"""
End-to-End Verification Script for Non-Ollama Providers

This script tests the full document analysis workflow with non-Ollama providers
(GPT, Claude API, GLM) to verify complete functionality.

Usage:
    python test_e2e_verification.py --test-provider       # Test provider creation only
    python test_e2e_verification.py --max-docs 1          # Full E2E test with 1 document
    python test_e2e_verification.py --max-docs 5 --debug  # Full test with 5 documents, debug logging
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from llm_providers import create_llm_provider

# ANSI color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.RESET}")

def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}\n")

def test_provider_creation(provider_type, config):
    """Test that the provider can be created successfully."""
    print_header(f"TEST 1: Provider Creation ({provider_type.upper()})")

    try:
        provider = create_llm_provider(provider_type, config)
        print_success(f"Provider created: {type(provider).__name__}")
        print_info(f"   Model: {provider.model}")
        print_info(f"   URL: {provider.url}")

        # Verify provider has required methods
        assert hasattr(provider, 'evaluate_content'), "Missing evaluate_content method"
        assert hasattr(provider, 'generate_title'), "Missing generate_title method"
        print_success("Provider has all required methods")

        return True, provider
    except Exception as e:
        print_error(f"Provider creation failed: {e}")
        return False, None

def test_provider_evaluation(provider, provider_type):
    """Test that the provider can evaluate document content."""
    print_header(f"TEST 2: Content Evaluation ({provider_type.upper()})")

    test_content = """
    This is a well-written, clear document with meaningful content.
    It contains proper grammar, logical organization, and valuable information.
    The text is coherent and serves a clear purpose.
    """

    test_prompt = """
    Please review the following document content and determine if it is of low quality or high quality.
    Low quality means the content contains many meaningless or unrelated words or sentences.
    High quality means the content is clear, organized, and meaningful.
    Respond strictly with "low quality" or "high quality".
    """

    try:
        print_info("Sending test content to provider for evaluation...")
        result = provider.evaluate_content(test_content, test_prompt, doc_id=999)

        if result in ["low quality", "high quality"]:
            print_success(f"Evaluation result: {result}")
            return True
        else:
            print_warning(f"Unexpected result: '{result}' (expected 'low quality' or 'high quality')")
            return False
    except Exception as e:
        print_error(f"Evaluation failed: {e}")
        import traceback
        print_info(f"Traceback: {traceback.format_exc()}")
        return False

def test_provider_title_generation(provider, provider_type):
    """Test that the provider can generate titles."""
    print_header(f"TEST 3: Title Generation ({provider_type.upper()})")

    test_content = """
    Financial Report Q4 2024

    This document presents the quarterly financial results for Q4 2024.
    Revenue increased by 15% compared to the previous quarter.
    Net profit reached $2.5 million.
    """

    title_prompt = """
    You are an expert at creating meaningful document titles.
    Analyze the following content and create a concise, descriptive title
    that accurately summarizes the content.
    The title should not exceed 100 characters.
    Respond only with the title, without explanation or additional text.

    Content:
    """

    try:
        print_info("Sending request to provider for title generation...")
        title = provider.generate_title(title_prompt, test_content)

        if title and len(title.strip()) > 0:
            print_success(f"Generated title: '{title}'")
            print_info(f"   Title length: {len(title)} characters")
            if len(title) <= 100:
                print_success("Title length is within 100 character limit")
            else:
                print_warning(f"Title exceeds 100 character limit: {len(title)}")
            return True
        else:
            print_error("Provider returned empty title")
            return False
    except Exception as e:
        print_error(f"Title generation failed: {e}")
        import traceback
        print_info(f"Traceback: {traceback.format_exc()}")
        return False

def test_configuration():
    """Test that environment is properly configured."""
    print_header("TEST 0: Configuration Check")

    load_dotenv()

    # Check required variables
    required_vars = {
        'API_URL': 'Paperless-ngx API URL',
        'API_TOKEN': 'Paperless-ngx API Token',
        'LOW_QUALITY_TAG_ID': 'Low Quality Tag ID',
        'HIGH_QUALITY_TAG_ID': 'High Quality Tag ID'
    }

    all_configured = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print_success(f"{description} ({var}): {'***' if 'TOKEN' in var or 'KEY' in var else value}")
        else:
            print_error(f"{description} ({var}) is not configured")
            all_configured = False

    # Check provider configuration
    provider_type = os.getenv('LLM_PROVIDER', 'ollama').lower()
    print_info(f"Selected LLM Provider: {provider_type.upper()}")

    provider_configs = {
        'gpt': ['GPT_API_KEY', 'GPT_MODEL'],
        'claude_api': ['CLAUDE_API_KEY', 'CLAUDE_MODEL'],
        'claude_code': ['CLAUDE_CODE_API_KEY', 'CLAUDE_CODE_MODEL'],
        'glm': ['GLM_API_KEY', 'GLM_MODEL'],
        'ollama': ['OLLAMA_URL', 'OLLAMA_ENDPOINT', 'MODEL_NAME']
    }

    if provider_type in provider_configs:
        for var in provider_configs[provider_type]:
            value = os.getenv(var)
            if value:
                print_success(f"{var}: {'***' if 'KEY' in var else value}")
            else:
                print_error(f"{var} is not configured")
                all_configured = False
    else:
        print_error(f"Unknown provider type: {provider_type}")
        return False, None, {}

    if not all_configured:
        print_warning("Some configuration is missing. Tests may fail.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False, None, {}

    # Build provider config
    config = {}
    if provider_type == 'gpt':
        config = {'api_key': os.getenv('GPT_API_KEY'), 'model': os.getenv('GPT_MODEL')}
    elif provider_type == 'claude_api':
        config = {'api_key': os.getenv('CLAUDE_API_KEY'), 'model': os.getenv('CLAUDE_MODEL')}
    elif provider_type == 'claude_code':
        config = {'api_key': os.getenv('CLAUDE_CODE_API_KEY'), 'model': os.getenv('CLAUDE_CODE_MODEL')}
    elif provider_type == 'glm':
        config = {'api_key': os.getenv('GLM_API_KEY'), 'model': os.getenv('GLM_MODEL')}
    elif provider_type == 'ollama':
        config = {
            'url': os.getenv('OLLAMA_URL'),
            'endpoint': os.getenv('OLLAMA_ENDPOINT'),
            'model': os.getenv('MODEL_NAME')
        }

    return True, provider_type, config

def run_full_e2e_test(max_documents):
    """Run the full end-to-end workflow."""
    print_header("TEST 4: Full E2E Workflow")

    print_info("This will run the full document analysis workflow.")
    print_info(f"MAX_DOCUMENTS is set to: {max_documents}")
    print_warning("Make sure you have documents in your Paperless-ngx instance!")

    response = input("Proceed with full E2E test? (y/n): ")
    if response.lower() != 'y':
        print_info("Skipping full E2E test.")
        return True

    try:
        # Import main module and run
        import main

        # Temporarily override MAX_DOCUMENTS
        original_max = os.getenv('MAX_DOCUMENTS')
        os.environ['MAX_DOCUMENTS'] = str(max_documents)

        print_info("Starting full workflow...")
        main.main()

        # Restore original value
        if original_max:
            os.environ['MAX_DOCUMENTS'] = original_max
        else:
            os.environ.pop('MAX_DOCUMENTS', None)

        print_success("Full E2E workflow completed")
        return True
    except Exception as e:
        print_error(f"Full E2E test failed: {e}")
        import traceback
        print_info(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='End-to-End Verification for Non-Ollama LLM Providers'
    )
    parser.add_argument(
        '--test-provider',
        action='store_true',
        help='Test provider creation and basic functionality only (skip full E2E)'
    )
    parser.add_argument(
        '--max-docs',
        type=int,
        default=1,
        help='Maximum number of documents to process in full E2E test (default: 1)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    if args.debug:
        os.environ['LOG_LEVEL'] = 'DEBUG'

    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "E2E VERIFICATION SCRIPT" + " " * 37 + "║")
    print("║" + " " * 10 + "Custom LLM Provider Support" + " " * 36 + "║")
    print("╚" + "=" * 78 + "╝")
    print(f"{Colors.RESET}\n")

    # Test 0: Configuration
    config_ok, provider_type, config = test_configuration()
    if not config_ok:
        print_error("Configuration check failed. Exiting.")
        sys.exit(1)

    # Test 1: Provider Creation
    provider_ok, provider = test_provider_creation(provider_type, config)
    if not provider_ok:
        print_error("Provider creation failed. Exiting.")
        sys.exit(1)

    # If --test-provider flag, run Tests 2 and 3 then exit
    if args.test_provider:
        print_info("Running provider functionality tests only (--test-provider flag set)")

        eval_ok = test_provider_evaluation(provider, provider_type)
        title_ok = test_provider_title_generation(provider, provider_type)

        print_header("TEST SUMMARY")
        print_success(f"Provider Creation: {'PASS' if provider_ok else 'FAIL'}")
        print_success(f"Content Evaluation: {'PASS' if eval_ok else 'FAIL'}")
        print_success(f"Title Generation: {'PASS' if title_ok else 'FAIL'}")

        all_passed = provider_ok and eval_ok and title_ok
        if all_passed:
            print_success("\n🎉 ALL TESTS PASSED!")
            sys.exit(0)
        else:
            print_error("\n❌ SOME TESTS FAILED")
            sys.exit(1)

    # Run Tests 2 and 3
    eval_ok = test_provider_evaluation(provider, provider_type)
    title_ok = test_provider_title_generation(provider, provider_type)

    # Test 4: Full E2E Workflow
    e2e_ok = run_full_e2e_test(args.max_docs)

    # Final Summary
    print_header("FINAL TEST SUMMARY")
    print(f"Provider: {Colors.BOLD}{provider_type.upper()}{Colors.RESET}")
    print(f"Provider Creation:     {Colors.GREEN}PASS{Colors.RESET if provider_ok else Colors.RED}FAIL{Colors.RESET}")
    print(f"Content Evaluation:    {Colors.GREEN}PASS{Colors.RESET if eval_ok else Colors.RED}FAIL{Colors.RESET}")
    print(f"Title Generation:      {Colors.GREEN}PASS{Colors.RESET if title_ok else Colors.RED}FAIL{Colors.RESET}")
    print(f"Full E2E Workflow:     {Colors.GREEN}PASS{Colors.RESET if e2e_ok else Colors.RED}FAIL{Colors.RESET}")

    all_passed = provider_ok and eval_ok and title_ok and e2e_ok

    if all_passed:
        print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 ALL TESTS PASSED! 🎉{Colors.RESET}\n")
        print_success("The non-Ollama provider is working correctly!")
        print_info("You can now use this provider in production.")
        sys.exit(0)
    else:
        print(f"\n{Colors.BOLD}{Colors.RED}❌ SOME TESTS FAILED{Colors.RESET}\n")
        print_error("Please check the errors above and:")
        print("  1. Verify your API credentials are correct")
        print("  2. Check your network connection")
        print("  3. Ensure the API service is available")
        print("  4. Review E2E_VERIFICATION_GUIDE.md for troubleshooting")
        sys.exit(1)

if __name__ == "__main__":
    main()
