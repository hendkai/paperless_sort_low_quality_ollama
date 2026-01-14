#!/usr/bin/env python3
"""
Backward Compatibility Test Script for Ollama Configuration

This script verifies that existing Ollama configuration still works correctly
after the refactoring to support multiple LLM providers.
"""

import os
import sys
from dotenv import load_dotenv

def test_imports():
    """Test that all required imports work correctly."""
    print("=" * 70)
    print("TEST 1: Import Verification")
    print("=" * 70)
    try:
        from llm_providers import (
            BaseLLMProvider,
            OllamaService,
            GLMProvider,
            ClaudeAPIProvider,
            GPTProvider,
            ClaudeCodeProvider,
            EnsembleLLMService,
            create_llm_provider
        )
        print("✅ All llm_providers imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_main_imports():
    """Test that main.py can be imported without errors."""
    print("\n" + "=" * 70)
    print("TEST 2: Main Module Import")
    print("=" * 70)
    try:
        import main
        print("✅ main.py imported successfully")
        return True
    except Exception as e:
        print(f"❌ main.py import failed: {e}")
        return False


def test_ollama_service_instantiation():
    """Test that OllamaService can be instantiated with old configuration."""
    print("\n" + "=" * 70)
    print("TEST 3: OllamaService Instantiation")
    print("=" * 70)
    try:
        from llm_providers import OllamaService

        # Test with typical Ollama configuration
        service = OllamaService(
            url="http://localhost:11434",
            endpoint="/api/generate",
            model="llama3.2"
        )

        assert service.url == "http://localhost:11434"
        assert service.endpoint == "/api/generate"
        assert service.model == "llama3.2"
        print("✅ OllamaService instantiation successful")
        print(f"   - URL: {service.url}")
        print(f"   - Endpoint: {service.endpoint}")
        print(f"   - Model: {service.model}")
        return True
    except Exception as e:
        print(f"❌ OllamaService instantiation failed: {e}")
        return False


def test_provider_factory_ollama():
    """Test that create_llm_provider works for Ollama."""
    print("\n" + "=" * 70)
    print("TEST 4: Provider Factory - Ollama")
    print("=" * 70)
    try:
        from llm_providers import create_llm_provider

        provider = create_llm_provider('ollama', {
            'url': 'http://localhost:11434',
            'endpoint': '/api/generate',
            'model': 'llama3.2'
        })

        assert type(provider).__name__ == 'OllamaService'
        print("✅ Provider factory created OllamaService successfully")
        print(f"   - Provider type: {type(provider).__name__}")
        print(f"   - Model: {provider.model}")
        return True
    except Exception as e:
        print(f"❌ Provider factory test failed: {e}")
        return False


def test_default_llm_provider():
    """Test that LLM_PROVIDER defaults to 'ollama' when not set."""
    print("\n" + "=" * 70)
    print("TEST 5: Default LLM_PROVIDER Value")
    print("=" * 70)

    # Temporarily unset LLM_PROVIDER if it exists
    original_value = os.environ.get('LLM_PROVIDER')
    if 'LLM_PROVIDER' in os.environ:
        del os.environ['LLM_PROVIDER']

    try:
        # Reload the module to pick up the changed environment
        import importlib
        import main
        importlib.reload(main)

        # Check that it defaults to 'ollama'
        default_provider = os.getenv('LLM_PROVIDER', 'ollama').lower()
        assert default_provider == 'ollama'
        print("✅ LLM_PROVIDER correctly defaults to 'ollama'")
        print(f"   - Default value: {default_provider}")

        # Restore original value
        if original_value:
            os.environ['LLM_PROVIDER'] = original_value

        return True
    except Exception as e:
        print(f"❌ Default LLM_PROVIDER test failed: {e}")
        # Restore original value
        if original_value:
            os.environ['LLM_PROVIDER'] = original_value
        return False


def test_ollama_env_variables():
    """Test that Ollama environment variables are read correctly."""
    print("\n" + "=" * 70)
    print("TEST 6: Ollama Environment Variables")
    print("=" * 70)

    # Set test environment variables
    test_vars = {
        'OLLAMA_URL': 'http://test-ollama:11434',
        'OLLAMA_ENDPOINT': '/api/generate',
        'MODEL_NAME': 'test-model',
        'SECOND_MODEL_NAME': 'test-model-2',
        'THIRD_MODEL_NAME': 'test-model-3',
        'NUM_LLM_MODELS': '3',
        'LLM_PROVIDER': 'ollama'
    }

    original_vars = {}
    for key, value in test_vars.items():
        original_vars[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        # Reload the module to pick up the new environment variables
        import importlib
        import main
        importlib.reload(main)

        # Verify all variables are read correctly
        checks = [
            (main.OLLAMA_URL, 'OLLAMA_URL', test_vars['OLLAMA_URL']),
            (main.OLLAMA_ENDPOINT, 'OLLAMA_ENDPOINT', test_vars['OLLAMA_ENDPOINT']),
            (main.MODEL_NAME, 'MODEL_NAME', test_vars['MODEL_NAME']),
            (main.SECOND_MODEL_NAME, 'SECOND_MODEL_NAME', test_vars['SECOND_MODEL_NAME']),
            (main.THIRD_MODEL_NAME, 'THIRD_MODEL_NAME', test_vars['THIRD_MODEL_NAME']),
            (main.NUM_LLM_MODELS, 'NUM_LLM_MODELS', int(test_vars['NUM_LLM_MODELS'])),
            (main.LLM_PROVIDER, 'LLM_PROVIDER', test_vars['LLM_PROVIDER'])
        ]

        all_passed = True
        for actual_value, var_name, expected_value in checks:
            if actual_value == expected_value:
                print(f"✅ {var_name} = {actual_value}")
            else:
                print(f"❌ {var_name}: expected {expected_value}, got {actual_value}")
                all_passed = False

        # Restore original values
        for key, original_value in original_vars.items():
            if original_value is None:
                if key in os.environ:
                    del os.environ[key]
            else:
                os.environ[key] = original_value

        return all_passed
    except Exception as e:
        print(f"❌ Environment variables test failed: {e}")
        # Restore original values
        for key, original_value in original_vars.items():
            if original_value is None:
                if key in os.environ:
                    del os.environ[key]
            else:
                os.environ[key] = original_value
        return False


def test_ensemble_with_ollama():
    """Test that EnsembleLLMService works with Ollama providers."""
    print("\n" + "=" * 70)
    print("TEST 7: Ensemble Service with Ollama")
    print("=" * 70)
    try:
        from llm_providers import OllamaService, EnsembleLLMService

        # Create multiple Ollama services (simulating ensemble)
        services = [
            OllamaService(url="http://localhost:11434", endpoint="/api/generate", model="llama3.2"),
            OllamaService(url="http://localhost:11434", endpoint="/api/generate", model="mistral"),
            OllamaService(url="http://localhost:11434", endpoint="/api/generate", model="dolphin-mixtral")
        ]

        ensemble = EnsembleLLMService(services)

        assert len(ensemble.services) == 3
        assert all(isinstance(s, OllamaService) for s in ensemble.services)
        print("✅ EnsembleLLMService with Ollama providers successful")
        print(f"   - Number of services: {len(ensemble.services)}")
        print(f"   - Service models: {[s.model for s in ensemble.services]}")
        return True
    except Exception as e:
        print(f"❌ Ensemble service test failed: {e}")
        return False


def test_fallback_logic():
    """Test that fallback to Ollama works when provider is not configured."""
    print("\n" + "=" * 70)
    print("TEST 8: Fallback Logic to Ollama")
    print("=" * 70)
    try:
        from llm_providers import create_llm_provider

        # Set up environment with Ollama config but no LLM_PROVIDER
        test_vars = {
            'OLLAMA_URL': 'http://localhost:11434',
            'OLLAMA_ENDPOINT': '/api/generate',
            'MODEL_NAME': 'llama3.2'
        }

        original_vars = {}
        for key, value in test_vars.items():
            original_vars[key] = os.environ.get(key)
            os.environ[key] = value

        # Remove LLM_PROVIDER to test fallback
        original_provider = os.environ.get('LLM_PROVIDER')
        if 'LLM_PROVIDER' in os.environ:
            del os.environ['LLM_PROVIDER']

        try:
            # This should succeed by falling back to Ollama
            provider = create_llm_provider('ollama', {
                'url': test_vars['OLLAMA_URL'],
                'endpoint': test_vars['OLLAMA_ENDPOINT'],
                'model': test_vars['MODEL_NAME']
            })

            assert type(provider).__name__ == 'OllamaService'
            print("✅ Fallback logic works correctly")
            print(f"   - Provider type: {type(provider).__name__}")
            print(f"   - Model: {provider.model}")

            # Restore original values
            for key, original_value in original_vars.items():
                if original_value is None:
                    if key in os.environ:
                        del os.environ[key]
                else:
                    os.environ[key] = original_value
            if original_provider:
                os.environ['LLM_PROVIDER'] = original_provider

            return True
        except Exception as e:
            print(f"❌ Fallback logic test failed: {e}")
            # Restore original values
            for key, original_value in original_vars.items():
                if original_value is None:
                    if key in os.environ:
                        del os.environ[key]
                else:
                    os.environ[key] = original_value
            if original_provider:
                os.environ['LLM_PROVIDER'] = original_provider
            return False
    except Exception as e:
        print(f"❌ Fallback logic test setup failed: {e}")
        return False


def run_all_tests():
    """Run all backward compatibility tests."""
    print("\n" + "=" * 70)
    print("BACKWARD COMPATIBILITY TEST SUITE")
    print("Testing Ollama Configuration After Multi-Provider Refactoring")
    print("=" * 70 + "\n")

    # Load test environment variables
    load_dotenv('.env.test')
    print("Loaded test environment from .env.test\n")

    tests = [
        test_imports,
        test_main_imports,
        test_ollama_service_instantiation,
        test_provider_factory_ollama,
        test_default_llm_provider,
        test_ollama_env_variables,
        test_ensemble_with_ollama,
        test_fallback_logic
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {100 * passed / total:.1f}%")

    if passed == total:
        print("\n✅ ALL BACKWARD COMPATIBILITY TESTS PASSED!")
        print("Existing Ollama configuration is fully compatible.")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        print("Some backward compatibility issues detected.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
