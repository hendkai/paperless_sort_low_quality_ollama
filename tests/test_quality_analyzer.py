"""Unit tests for QualityAnalyzer module."""

import pytest
from unittest.mock import Mock, patch
from src.quality.analyzer import QualityAnalyzer
from src.llm.service import EnsembleOllamaService


class TestQualityAnalyzerInit:
    """Tests for QualityAnalyzer initialization."""

    def test_init(self):
        """Test analyzer initialization with correct parameters."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        quality_prompt = "Evaluate this content: "

        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt=quality_prompt
        )

        assert analyzer.llm_service == mock_llm_service
        assert analyzer.quality_prompt == quality_prompt

    def test_init_with_different_prompt(self):
        """Test analyzer initialization with different prompt."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        quality_prompt = "Determine quality: "

        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt=quality_prompt
        )

        assert analyzer.quality_prompt == "Determine quality: "


class TestEvaluate:
    """Tests for evaluate method."""

    @patch('src.quality.analyzer.logger')
    def test_evaluate_high_quality_with_consensus(self, mock_logger):
        """Test evaluation returning high quality with consensus."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        mock_llm_service.evaluate_content.return_value = ("high quality", True)

        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        quality_result, consensus = analyzer.evaluate("Test content", 123)

        assert quality_result == "high quality"
        assert consensus is True
        mock_llm_service.evaluate_content.assert_called_once_with(
            "Test content", "Evaluate: ", 123
        )

    @patch('src.quality.analyzer.logger')
    def test_evaluate_low_quality_with_consensus(self, mock_logger):
        """Test evaluation returning low quality with consensus."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        mock_llm_service.evaluate_content.return_value = ("low quality", True)

        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        quality_result, consensus = analyzer.evaluate("Test content", 456)

        assert quality_result == "low quality"
        assert consensus is True

    @patch('src.quality.analyzer.logger')
    def test_evaluate_without_consensus(self, mock_logger):
        """Test evaluation without consensus."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        mock_llm_service.evaluate_content.return_value = ("high quality", False)

        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        quality_result, consensus = analyzer.evaluate("Test content", 789)

        assert quality_result == "high quality"
        assert consensus is False

    @patch('src.quality.analyzer.logger')
    def test_evaluate_normalizes_response(self, mock_logger):
        """Test that evaluation normalizes responses."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        # Return response with different casing
        mock_llm_service.evaluate_content.return_value = ("HIGH QUALITY", True)

        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        quality_result, consensus = analyzer.evaluate("Test content", 100)

        # Should normalize to lowercase
        assert quality_result == "high quality"
        assert consensus is True

    @patch('src.quality.analyzer.logger')
    def test_evaluate_with_invalid_response(self, mock_logger):
        """Test evaluation when response is invalid."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        mock_llm_service.evaluate_content.return_value = ("invalid response", True)

        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        quality_result, consensus = analyzer.evaluate("Test content", 200)

        # Should return empty string for invalid response
        assert quality_result == ""
        assert consensus is True

    @patch('src.quality.analyzer.logger')
    def test_evaluate_with_empty_response(self, mock_logger):
        """Test evaluation when response is empty."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        mock_llm_service.evaluate_content.return_value = ("", False)

        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        quality_result, consensus = analyzer.evaluate("Test content", 300)

        assert quality_result == ""
        assert consensus is False

    @patch('src.quality.analyzer.logger')
    def test_evaluate_partial_match(self, mock_logger):
        """Test evaluation when response contains quality term."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        # Response contains "high quality" but isn't exact match
        mock_llm_service.evaluate_content.return_value = (
            "The document appears to be high quality based on content", True
        )

        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        quality_result, consensus = analyzer.evaluate("Test content", 400)

        # Should extract "high quality" from response
        assert quality_result == "high quality"
        assert consensus is True


class TestValidateQualityResponse:
    """Tests for _validate_quality_response method."""

    def test_validate_exact_high_quality(self):
        """Test validation with exact 'high quality' match."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        result = analyzer._validate_quality_response("high quality")
        assert result == "high quality"

    def test_validate_exact_low_quality(self):
        """Test validation with exact 'low quality' match."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        result = analyzer._validate_quality_response("low quality")
        assert result == "low quality"

    def test_validate_case_insensitive(self):
        """Test that validation is case-insensitive."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        # Test various case combinations
        assert analyzer._validate_quality_response("HIGH QUALITY") == "high quality"
        assert analyzer._validate_quality_response("High Quality") == "high quality"
        assert analyzer._validate_quality_response("LoW qUaliTy") == "low quality"

    def test_validate_with_whitespace(self):
        """Test validation with extra whitespace."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        result = analyzer._validate_quality_response("  high quality  ")
        assert result == "high quality"

    def test_validate_partial_match_high_quality(self):
        """Test validation with partial match for high quality."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        result = analyzer._validate_quality_response("This is high quality material")
        assert result == "high quality"

    def test_validate_partial_match_low_quality(self):
        """Test validation with partial match for low quality."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        result = analyzer._validate_quality_response("This is low quality data")
        assert result == "low quality"

    def test_validate_empty_response(self):
        """Test validation with empty response."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        result = analyzer._validate_quality_response("")
        assert result == ""

    def test_validate_none_response(self):
        """Test validation with None response."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        result = analyzer._validate_quality_response(None)
        assert result == ""

    def test_validate_invalid_response(self):
        """Test validation with invalid response."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        result = analyzer._validate_quality_response("This is a medium quality document")
        assert result == ""

    def test_validate_both_quality_terms(self):
        """Test validation when both quality terms are present."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        # When both are present, should match "high quality" first (appears first in logic)
        result = analyzer._validate_quality_response("This has both high quality and low quality")
        assert result == "high quality"


class TestDetermineTagAction:
    """Tests for determine_tag_action method."""

    @patch('src.quality.analyzer.logger')
    def test_determine_tag_low_quality(self, mock_logger):
        """Test tag action for low quality."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        action, should_process = analyzer.determine_tag_action("low quality", True)

        assert action == "tag_low"
        assert should_process is True

    @patch('src.quality.analyzer.logger')
    def test_determine_tag_high_quality(self, mock_logger):
        """Test tag action for high quality."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        action, should_process = analyzer.determine_tag_action("high quality", True)

        assert action == "tag_high"
        assert should_process is True

    @patch('src.quality.analyzer.logger')
    def test_determine_tag_no_consensus(self, mock_logger):
        """Test tag action when no consensus is reached."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        action, should_process = analyzer.determine_tag_action("high quality", False)

        assert action == "skip"
        assert should_process is False

    @patch('src.quality.analyzer.logger')
    def test_determine_tag_invalid_quality(self, mock_logger):
        """Test tag action when quality result is invalid."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        action, should_process = analyzer.determine_tag_action("", True)

        assert action == "skip"
        assert should_process is False

    @patch('src.quality.analyzer.logger')
    def test_determine_tag_invalid_quality_no_consensus(self, mock_logger):
        """Test tag action with invalid quality and no consensus."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        action, should_process = analyzer.determine_tag_action("invalid", False)

        assert action == "skip"
        assert should_process is False


class TestIsHighQuality:
    """Tests for is_high_quality method."""

    def test_is_high_quality_true(self):
        """Test is_high_quality returns True for high quality."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        assert analyzer.is_high_quality("high quality") is True

    def test_is_high_quality_false_low_quality(self):
        """Test is_high_quality returns False for low quality."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        assert analyzer.is_high_quality("low quality") is False

    def test_is_high_quality_false_empty(self):
        """Test is_high_quality returns False for empty string."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        assert analyzer.is_high_quality("") is False

    def test_is_high_quality_case_sensitive(self):
        """Test is_high_quality is case-sensitive."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        # Should return False for incorrect case (expects exact "high quality")
        assert analyzer.is_high_quality("HIGH QUALITY") is False
        assert analyzer.is_high_quality("High Quality") is False


class TestIsLowQuality:
    """Tests for is_low_quality method."""

    def test_is_low_quality_true(self):
        """Test is_low_quality returns True for low quality."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        assert analyzer.is_low_quality("low quality") is True

    def test_is_low_quality_false_high_quality(self):
        """Test is_low_quality returns False for high quality."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        assert analyzer.is_low_quality("high quality") is False

    def test_is_low_quality_false_empty(self):
        """Test is_low_quality returns False for empty string."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        assert analyzer.is_low_quality("") is False

    def test_is_low_quality_case_sensitive(self):
        """Test is_low_quality is case-sensitive."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        # Should return False for incorrect case (expects exact "low quality")
        assert analyzer.is_low_quality("LOW QUALITY") is False
        assert analyzer.is_low_quality("Low Quality") is False


class TestQualityAnalyzerIntegration:
    """Integration tests for QualityAnalyzer workflow."""

    @patch('src.quality.analyzer.logger')
    def test_full_workflow_high_quality(self, mock_logger):
        """Test complete workflow for high quality document."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        mock_llm_service.evaluate_content.return_value = ("high quality", True)

        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        # Evaluate
        quality, consensus = analyzer.evaluate("Great document content", 1)

        # Determine action
        action, should_process = analyzer.determine_tag_action(quality, consensus)

        # Check quality
        is_high = analyzer.is_high_quality(quality)
        is_low = analyzer.is_low_quality(quality)

        assert quality == "high quality"
        assert consensus is True
        assert action == "tag_high"
        assert should_process is True
        assert is_high is True
        assert is_low is False

    @patch('src.quality.analyzer.logger')
    def test_full_workflow_low_quality(self, mock_logger):
        """Test complete workflow for low quality document."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        mock_llm_service.evaluate_content.return_value = ("low quality", True)

        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        # Evaluate
        quality, consensus = analyzer.evaluate("Poor document content", 2)

        # Determine action
        action, should_process = analyzer.determine_tag_action(quality, consensus)

        # Check quality
        is_high = analyzer.is_high_quality(quality)
        is_low = analyzer.is_low_quality(quality)

        assert quality == "low quality"
        assert consensus is True
        assert action == "tag_low"
        assert should_process is True
        assert is_high is False
        assert is_low is True

    @patch('src.quality.analyzer.logger')
    def test_full_workflow_no_consensus(self, mock_logger):
        """Test complete workflow when no consensus is reached."""
        mock_llm_service = Mock(spec=EnsembleOllamaService)
        mock_llm_service.evaluate_content.return_value = ("high quality", False)

        analyzer = QualityAnalyzer(
            llm_service=mock_llm_service,
            quality_prompt="Evaluate: "
        )

        # Evaluate
        quality, consensus = analyzer.evaluate("Ambiguous content", 3)

        # Determine action
        action, should_process = analyzer.determine_tag_action(quality, consensus)

        assert quality == "high quality"
        assert consensus is False
        assert action == "skip"
        assert should_process is False
