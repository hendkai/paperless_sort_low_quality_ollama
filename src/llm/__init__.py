"""
LLM service module for interacting with Ollama.

This module provides classes for evaluating document quality
using local LLM models through Ollama.
"""

from src.llm.service import OllamaService, EnsembleOllamaService

__all__ = ["OllamaService", "EnsembleOllamaService"]
