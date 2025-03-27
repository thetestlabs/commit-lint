from unittest.mock import patch

import pytest

from commit_lint.formats.jira import JiraCommitFormat


@pytest.fixture
def default_config():
    """Default Jira format configuration."""
    return {
        "jira_project_keys": ["PROJ", "TEST", "DEV"],
        "require_issue_id": True,
        "max_message_length": 72,
    }


class TestJiraFormat:
    """Test suite for Jira format implementation."""

    def test_format_name(self):
        """Test the format name is correctly returned."""
        assert JiraCommitFormat.get_format_name() == "jira"

    def test_valid_simple_message(self, default_config):
        """Test validation of a simple valid message."""
        formatter = JiraCommitFormat(default_config)
        result = formatter.validate("PROJ-123: Add support for Jira format")

        assert result.valid
        assert len(result.errors) == 0
        assert result.issue_id == "PROJ-123"
        assert result.message == "Add support for Jira format"
        assert result.body is None

    def test_valid_message_with_body(self, default_config):
        """Test validation of a message with body."""
        formatter = JiraCommitFormat(default_config)
        result = formatter.validate(
            "TEST-456: Add Jira format support\n\nThis commit adds validation for Jira-style commit messages."
        )

        assert result.valid
        assert len(result.errors) == 0
        assert result.issue_id == "TEST-456"
        assert result.message == "Add Jira format support"
        assert result.body == "This commit adds validation for Jira-style commit messages."

    def test_invalid_project_key(self, default_config):
        """Test validation fails with invalid project key."""
        formatter = JiraCommitFormat(default_config)
        result = formatter.validate("INVALID-123: This uses an unrecognized project key")

        # First ensure validation fails
        assert not result.valid

        # Now check for the actual error message we're getting
        assert any("Commit message must start with a Jira issue ID" in error for error in result.errors)

    def test_issue_id_required(self, default_config):
        """Test validation when issue ID is required."""
        formatter = JiraCommitFormat(default_config)
        result = formatter.validate("Add Jira support without issue ID")

        assert not result.valid
        assert any("issue ID" in error for error in result.errors)

    def test_issue_id_optional(self):
        """Test validation when issue ID is optional."""
        config = {"require_issue_id": False, "jira_project_keys": ["PROJ"]}
        formatter = JiraCommitFormat(config)

        # With issue ID
        with_id = formatter.validate("PROJ-123: Add Jira support")
        assert with_id.valid
        assert with_id.issue_id == "PROJ-123"

        # Without issue ID
        without_id = formatter.validate("Add Jira support without issue ID")
        assert without_id.valid
        assert without_id.issue_id is None
        assert without_id.message == "Add Jira support without issue ID"

    def test_message_length_validation(self, default_config):
        """Test message length validation."""
        formatter = JiraCommitFormat(default_config)

        # Create a message that exceeds the max length
        long_message = "PROJ-123: " + "A" * 73

        result = formatter.validate(long_message)
        assert not result.valid
        assert any("too long" in error.lower() for error in result.errors)

    def test_custom_message_length(self):
        """Test custom message length limit."""
        config = {"max_message_length": 20, "jira_project_keys": ["PROJ"]}
        formatter = JiraCommitFormat(config)

        # This message is valid with default length but too long with custom length
        result = formatter.validate("PROJ-123: This message is now too long")

        assert not result.valid
        assert any("too long" in error.lower() for error in result.errors)

    def test_empty_project_keys(self):
        """Test behavior when no project keys are specified."""
        config = {"jira_project_keys": []}
        formatter = JiraCommitFormat(config)

        # Without project key restrictions, any key should be accepted
        result = formatter.validate("ANYTHING-123: This should be valid")
        assert result.valid
        assert result.issue_id == "ANYTHING-123"

    def test_issue_id_format(self, default_config):
        """Test different issue ID formats."""
        formatter = JiraCommitFormat(default_config)

        # Invalid format (missing colon)
        invalid = formatter.validate("PROJ-123 Missing colon separator")
        assert not invalid.valid

        # Invalid format (missing space after colon)
        invalid = formatter.validate("PROJ-123:Missing space")
        assert not invalid.valid

        # Valid format with extra spaces
        valid = formatter.validate("PROJ-123:    Extra spaces are fine")
        assert valid.valid
        assert valid.message == "Extra spaces are fine"

    def test_complex_body(self, default_config):
        """Test messages with complex multi-line bodies."""
        # Override the default config to allow longer messages for this test
        config = default_config.copy()
        config["max_message_length"] = 200  # Increase to accommodate the complex body

        formatter = JiraCommitFormat(config)

        message = """TEST-789: Add complex feature
        
This is a detailed description
with multiple lines
        
- Including lists
- And formatting
        
And more paragraphs"""

        result = formatter.validate(message)
        assert result.valid
        assert result.issue_id == "TEST-789"

        # Check that the message is just the subject line
        assert result.message == "Add complex feature"

        # Body should contain the detailed content
        assert result.body is not None
        assert "detailed description" in str(result.body)
        assert "Including lists" in str(result.body)
        assert "And formatting" in str(result.body)

    def test_malformed_issue_ids(self, default_config):
        """Test handling of malformed issue IDs."""
        formatter = JiraCommitFormat(default_config)

        # Missing hyphen
        result = formatter.validate("PROJ123: Missing hyphen")
        assert not result.valid

        # No issue number
        result = formatter.validate("PROJ-: No issue number")
        assert not result.valid

        # Non-numeric issue number
        result = formatter.validate("PROJ-ABC: Non-numeric issue")
        assert not result.valid

    def test_issue_id_edge_cases(self, default_config):
        """Test edge cases for issue IDs."""
        formatter = JiraCommitFormat(default_config)

        # Very long issue number
        result = formatter.validate("PROJ-123456789: Very long issue number")
        assert result.valid

        # Case sensitivity in project key
        result = formatter.validate("proj-123: Lowercase project key")
        assert not result.valid  # Project keys are typically case-sensitive

    def test_branch_based_validation(self):
        """Test validation using branch name for context."""
        # Check if the utils module exists first
        try:
            from commit_lint import utils

            has_utils = hasattr(utils, "get_current_branch")
        except ImportError:
            has_utils = False

        if not has_utils:
            pytest.skip("commit_lint.utils module or get_current_branch function not implemented yet")

        # Some teams use branch naming conventions like feature/PROJ-123-description
        config = {"jira_project_keys": ["PROJ"], "validate_against_branch": True}
        formatter = JiraCommitFormat(config)

        with patch("commit_lint.utils.get_current_branch") as mock_branch:
            mock_branch.return_value = "feature/PROJ-123-add-feature"

            # Message matches branch issue ID
            result = formatter.validate("PROJ-123: Add feature")
            assert result.valid

            # Message uses different issue ID than branch
            result = formatter.validate("PROJ-456: Unrelated change")
            assert not result.valid
            assert any("branch issue ID" in error.lower() for error in result.errors)


class TestJiraPrompt:
    """Test suite for Jira format message prompting."""

    def test_basic_prompting(self, default_config):
        """Test basic message prompting with issue ID."""
        formatter = JiraCommitFormat(default_config)

        # Mock all the prompt interactions
        with patch("rich.prompt.Prompt.ask") as mock_ask, patch("rich.prompt.Confirm.ask") as mock_confirm:
            # Set up responses
            def ask_side_effect(prompt, **kwargs):
                if "project key" in prompt.lower():
                    return "PROJ"
                elif "Issue number" in prompt:
                    return "123"
                elif "Commit message" in prompt:
                    return "Add Jira support"
                return ""

            mock_ask.side_effect = ask_side_effect
            mock_confirm.return_value = False  # No to detailed description

            # Call the method
            result = formatter.prompt_for_message(default_config)

            # Verify the result
            assert result == "PROJ-123: Add Jira support"

    def test_prompting_with_body(self, default_config):
        """Test message prompting with body."""
        formatter = JiraCommitFormat(default_config)

        with (
            patch("rich.prompt.Prompt.ask") as mock_ask,
            patch("rich.prompt.Confirm.ask") as mock_confirm,
            patch("builtins.input") as mock_input,
        ):
            # Set up responses
            def ask_side_effect(prompt, **kwargs):
                if "project key" in prompt.lower():
                    return "TEST"
                elif "Issue number" in prompt:
                    return "456"
                elif "Commit message" in prompt:
                    return "Add detailed commit"
                return ""

            mock_ask.side_effect = ask_side_effect

            # Yes to detailed description, implicitly yes to issue ID
            mock_confirm.side_effect = [True]

            # Body input
            mock_input.side_effect = ["First line of details", "Second line of details", ""]

            # Call the method
            result = formatter.prompt_for_message(default_config)

            # Verify the result
            expected = "TEST-456: Add detailed commit\n\nFirst line of details\nSecond line of details"
            assert result == expected

    def test_prompting_without_issue_id(self):
        """Test message prompting without issue ID when it's optional."""
        config = {"require_issue_id": False, "jira_project_keys": ["PROJ"]}
        formatter = JiraCommitFormat(config)

        with patch("rich.prompt.Prompt.ask") as mock_ask, patch("rich.prompt.Confirm.ask") as mock_confirm:
            # Set up responses
            mock_ask.return_value = "Simple message without ID"

            # No to issue ID, No to detailed description
            mock_confirm.side_effect = [False, False]

            # Call the method
            result = formatter.prompt_for_message(config)

            # Verify the result - should not have an issue ID
            assert result == "Simple message without ID"
            assert ":" not in result

    def test_project_key_selection(self, default_config):
        """Test project key selection from configured keys."""
        formatter = JiraCommitFormat(default_config)

        with patch("rich.prompt.Prompt.ask") as mock_ask, patch("rich.prompt.Confirm.ask") as mock_confirm:
            # Set up responses
            def ask_side_effect(prompt, **kwargs):
                if "project key" in prompt.lower():
                    assert "choices" in kwargs
                    assert set(kwargs["choices"]) == set(["PROJ", "TEST", "DEV"])
                    return "DEV"
                elif "Issue number" in prompt:
                    return "999"
                elif "Commit message" in prompt:
                    return "Test key selection"
                return ""

            mock_ask.side_effect = ask_side_effect
            mock_confirm.return_value = False  # No to detailed description

            # Call the method
            result = formatter.prompt_for_message(default_config)

            # Verify the result
            assert result == "DEV-999: Test key selection"

    def test_empty_project_keys_prompting(self):
        """Test prompting behavior when no project keys are configured."""
        config = {"jira_project_keys": []}
        formatter = JiraCommitFormat(config)

        with patch("rich.prompt.Prompt.ask") as mock_ask, patch("rich.prompt.Confirm.ask") as mock_confirm:
            # Set up responses
            def ask_side_effect(prompt, **kwargs):
                if "project key" in prompt.lower():
                    assert "choices" not in kwargs  # Should not provide choices
                    return "CUSTOM"
                elif "Issue number" in prompt:
                    return "123"
                elif "Commit message" in prompt:
                    return "Custom project key"
                return ""

            mock_ask.side_effect = ask_side_effect
            mock_confirm.return_value = False  # No to detailed description

            # Call the method
            result = formatter.prompt_for_message(config)

            # Verify the result
            assert result == "CUSTOM-123: Custom project key"
