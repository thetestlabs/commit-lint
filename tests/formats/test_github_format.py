from unittest.mock import patch

import pytest

from commit_lint.formats.github import GitHubCommitFormat


@pytest.fixture
def default_config():
    """Default GitHub format configuration."""
    return {
        "max_subject_length": 72,
        "imperative_mood": True,
        "issue_reference_required": False,
        "keywords": ["Fixes", "Closes", "Resolves"],
    }


class TestGitHubFormat:
    """Test suite for GitHub format implementation."""

    def test_format_name(self):
        """Test the format name is correctly returned."""
        assert GitHubCommitFormat.get_format_name() == "github"

    def test_valid_simple_message(self, default_config):
        """Test validation of a simple valid message."""
        formatter = GitHubCommitFormat(default_config)
        result = formatter.validate("Add support for GitHub format")

        assert result.valid
        assert len(result.errors) == 0
        assert result.message == "Add support for GitHub format"
        assert result.issue_reference is None
        assert result.issue_keyword is None

    def test_valid_message_with_body(self, default_config):
        """Test validation of a message with body."""
        formatter = GitHubCommitFormat(default_config)
        result = formatter.validate(
            "Add GitHub format support\n\nThis commit adds validation for GitHub-style commit messages."
        )

        assert result.valid
        assert len(result.errors) == 0
        assert result.message == "Add GitHub format support"

    def test_valid_message_with_issue_reference(self, default_config):
        """Test validation of a message with issue reference."""
        formatter = GitHubCommitFormat(default_config)
        result = formatter.validate("Add GitHub format support\n\nFixes #123")

        assert result.valid
        assert result.issue_reference == "123"
        assert result.issue_keyword == "Fixes"

    def test_invalid_subject_length(self, default_config):
        """Test validation fails when subject line is too long."""
        formatter = GitHubCommitFormat(default_config)
        # Create a message with subject longer than 72 chars
        long_subject = "Add " + "very " * 20 + "long subject that exceeds the maximum length for GitHub commit messages"

        result = formatter.validate(long_subject)

        assert not result.valid
        assert any("too long" in error for error in result.errors)

    def test_custom_subject_length(self):
        """Test custom max_subject_length configuration."""
        # Set a very short max length
        config = {"max_subject_length": 20}
        formatter = GitHubCommitFormat(config)

        # This would be valid with default 72 chars
        result = formatter.validate("Add GitHub format support")

        assert not result.valid
        assert any("too long" in error for error in result.errors)

    def test_imperative_mood_validation(self, default_config):
        """Test imperative mood validation."""
        formatter = GitHubCommitFormat(default_config)

        # Valid imperative mood
        valid_result = formatter.validate("Add new feature")
        assert valid_result.valid

        # Invalid non-imperative mood
        invalid_result = formatter.validate("Added new feature")
        assert not invalid_result.valid
        assert any("imperative mood" in error for error in invalid_result.errors)

        invalid_result = formatter.validate("Fixed bug in parser")
        assert not invalid_result.valid
        assert any("imperative mood" in error for error in invalid_result.errors)

    def test_disable_imperative_mood(self):
        """Test that imperative mood validation can be disabled."""
        config = {"imperative_mood": False}
        formatter = GitHubCommitFormat(config)

        # Should pass even with non-imperative verb
        result = formatter.validate("Added new feature")
        assert result.valid

    def test_issue_reference_required(self):
        """Test validation when issue reference is required."""
        config = {"issue_reference_required": True}
        formatter = GitHubCommitFormat(config)

        # Without issue reference
        without_ref = formatter.validate("Add GitHub format support")
        assert not without_ref.valid
        assert any("issue reference" in error.lower() for error in without_ref.errors)

        # With issue reference
        with_ref = formatter.validate("Add GitHub format support\n\nFixes #123")
        assert with_ref.valid

    def test_custom_keywords(self):
        """Test that custom issue reference keywords are respected."""
        config = {"keywords": ["Related", "See"]}
        formatter = GitHubCommitFormat(config)

        # Using custom keyword
        result = formatter.validate("Add GitHub format support\n\nRelated #123")
        assert result.valid
        assert result.issue_keyword == "Related"
        assert result.issue_reference == "123"

        # Using standard keyword that's not in custom list
        result = formatter.validate("Add GitHub format support\n\nFixes #123")
        assert result.issue_reference is None  # Should not recognize "Fixes"

    def test_different_issue_reference_formats(self, default_config):
        """Test different formats of issue references."""
        formatter = GitHubCommitFormat(default_config)

        # With colon
        result = formatter.validate("Add support\n\nFixes: #123")
        assert result.valid
        assert result.issue_reference == "123"

        # Without leading space - this is actually considered valid but doesn't extract a reference
        result = formatter.validate("Add support\n\nFixes#123")
        assert result.valid  # The format is valid but doesn't match issue reference pattern
        assert result.issue_reference is None  # No issue reference extracted

        # In parentheses in subject - this is valid but doesn't get parsed as an issue reference
        result = formatter.validate("Add support (Fixes #123)")
        assert result.valid
        assert result.issue_reference is None  # Implementation doesn't extract references from subject line

        # Multiple issue references in body - should capture the first one
        result = formatter.validate("Add support\n\nFixes #123 and Closes #456")
        assert result.valid
        assert result.issue_reference == "123"
        assert result.issue_keyword == "Fixes"

    def test_issue_reference_patterns(self, default_config):
        """Test different issue reference patterns in detail."""
        formatter = GitHubCommitFormat(default_config)

        # Required format: keyword followed by space and # with issue number
        result = formatter.validate("Add support\n\nFixes #123")
        assert result.valid
        assert result.issue_reference == "123"
        assert result.issue_keyword == "Fixes"

        # Issue reference in parentheses in subject - this is valid but doesn't get parsed as an issue reference
        result = formatter.validate("Add support (Fixes #456)")
        assert result.valid
        assert result.issue_reference is None  # Implementation doesn't extract references from subject line

        # Multiple formats that should NOT match:
        formats = [
            "Add support\n\nRelated to issue 123",  # Missing # symbol
            "Add support\n\nSee PR 123",  # Not a recognized keyword
            "Add support\n\n#123",  # Missing keyword
        ]

        for msg in formats:
            result = formatter.validate(msg)
            assert result.valid  # Message is still valid
            assert result.issue_reference is None  # But no issue reference extracted

    def test_issue_reference_location(self, default_config):
        """Test where issue references are recognized."""
        formatter = GitHubCommitFormat(default_config)

        # Reference in body - should be recognized
        body_result = formatter.validate("Add feature\n\nFixes #123")
        assert body_result.valid
        assert body_result.issue_reference == "123"

        # Reference in subject line without parentheses - ALSO recognized
        subject_result = formatter.validate("Add feature Fixes #123")
        assert subject_result.valid
        assert subject_result.issue_reference == "123"  # Implementation DOES extract from subject

        # Reference in parentheses in subject - NOT recognized
        parens_result = formatter.validate("Add feature (Fixes #123)")
        assert parens_result.valid
        assert parens_result.issue_reference is None  # Implementation doesn't extract parenthesized references

        # Reference in both subject and body - should recognize the first one found
        both_result = formatter.validate("Add feature Fixes #123\n\nCloses #456")
        assert both_result.valid
        # Based on observed behavior - subject references are recognized first
        assert both_result.issue_reference == "123"


class TestGitHubPrompt:
    """Test suite for GitHub format message prompting."""

    def test_basic_prompting(self, default_config):
        """Test basic message prompting without body or references."""
        formatter = GitHubCommitFormat(default_config)

        # Mock all the prompt interactions
        with patch("rich.prompt.Prompt.ask") as mock_ask, patch("rich.prompt.Confirm.ask") as mock_confirm:
            # Set up mock responses
            mock_ask.return_value = "Add GitHub support"
            mock_confirm.return_value = False  # No to body and issue reference

            # Call the method
            result = formatter.prompt_for_message(default_config)

            # Verify the result
            assert result == "Add GitHub support"
            assert mock_ask.call_count == 1

    def test_prompting_with_body(self, default_config):
        """Test message prompting with body."""
        formatter = GitHubCommitFormat(default_config)

        with (
            patch("rich.prompt.Prompt.ask") as mock_ask,
            patch("rich.prompt.Confirm.ask") as mock_confirm,
            patch("builtins.input") as mock_input,
        ):
            # Set up mock responses
            mock_ask.return_value = "Add GitHub support"

            # First confirm is for body (True), second is for issue reference (False)
            mock_confirm.side_effect = [True, False]

            # Input for body lines, empty string signals end
            mock_input.side_effect = ["First line of body", "Second line of body", ""]

            # Call the method
            result = formatter.prompt_for_message(default_config)

            # Verify the result - subject + 2 newlines + body
            expected = "Add GitHub support\n\nFirst line of body\nSecond line of body"
            assert result == expected

    def test_prompting_with_issue_reference(self, default_config):
        """Test message prompting with issue reference."""
        formatter = GitHubCommitFormat(default_config)

        with patch("rich.prompt.Prompt.ask") as mock_ask, patch("rich.prompt.Confirm.ask") as mock_confirm:
            # Set up the responses for each prompt call
            def ask_side_effect(prompt, **kwargs):
                if prompt == "Subject":
                    return "Add GitHub support"
                elif prompt == "Reference keyword":
                    return "Fixes"
                elif prompt == "Issue number":
                    return "123"
                return ""  # Default

            mock_ask.side_effect = ask_side_effect

            # Body: No, Issue reference: Yes
            mock_confirm.side_effect = [False, True]

            # Call the method
            result = formatter.prompt_for_message(default_config)

            # Verify the result - should add issue reference in parentheses
            assert result == "Add GitHub support (Fixes #123)"

    def test_prompting_with_body_and_reference(self, default_config):
        """Test message prompting with both body and issue reference."""
        formatter = GitHubCommitFormat(default_config)

        with (
            patch("rich.prompt.Prompt.ask") as mock_ask,
            patch("rich.prompt.Confirm.ask") as mock_confirm,
            patch("builtins.input") as mock_input,
        ):
            # Set up the responses for each prompt call
            def ask_side_effect(prompt, **kwargs):
                if prompt == "Subject":
                    return "Add GitHub support"
                elif prompt == "Reference keyword":
                    return "Fixes"
                elif prompt == "Issue number":
                    return "123"
                return ""

            mock_ask.side_effect = ask_side_effect

            # Body: Yes, Issue reference: Yes
            mock_confirm.side_effect = [True, True]

            # Input for body lines
            mock_input.side_effect = ["Body text here", ""]

            # Call the method
            result = formatter.prompt_for_message(default_config)

            # Verify the result - should add issue reference at end of body
            assert result == "Add GitHub support\n\nBody text here\n\nFixes #123"

    def test_required_issue_reference(self):
        """Test prompting with required issue reference."""
        config = {"issue_reference_required": True, "keywords": ["Fixes", "Closes"]}
        formatter = GitHubCommitFormat(config)

        with patch("rich.prompt.Prompt.ask") as mock_ask, patch("rich.prompt.Confirm.ask") as mock_confirm:
            # Set up the responses
            def ask_side_effect(prompt, **kwargs):
                if prompt == "Subject":
                    return "Add GitHub support"
                elif prompt == "Reference keyword":
                    return "Fixes"
                elif prompt == "Issue number":
                    return "123"
                return ""

            mock_ask.side_effect = ask_side_effect

            # No to body
            mock_confirm.return_value = False

            # Call the method - should prompt for issue reference without asking
            result = formatter.prompt_for_message(config)

            # Should include issue reference
            assert "Fixes #123" in result
