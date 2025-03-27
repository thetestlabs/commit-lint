[![Actions status](https://github.com/astral-sh/ruff/workflows/CI/badge.svg)](https://github.com/astral-sh/ruff/actions)
[![codecov](https://codecov.io/gh/thetestlabs/commit-lint/graph/badge.svg?token=6DA1WBQZ8J)](https://codecov.io/gh/thetestlabs/commit-lint)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/12d604bbf25d48b2a987daddc5fe2876)](https://app.codacy.com/gh/thetestlabs/commit-lint/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
![GitHub commits since latest release (branch)](https://img.shields.io/github/commits-since/thetestlabs/commit-lint/latest/main)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PyPI Python Versions](https://img.shields.io/pypi/pyversions/poetry.svg)](https://pypi.python.org/pypi/poetry)
<a href="https://opensource.org/licenses/MIT"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-success.svg"></a>


# commit-lint
A configurable linter for better commit messages

# Commit Message Standards and Linting Rules

Here's a breakdown of the linting rules for each format supported by the tool:

## 1. Conventional Commits

```toml
[tool.commit_lint]
format_type = "conventional"
types = ["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"]
max_subject_length = 100
subject_case = "lower"
scope_required = false
allowed_breaking_changes = ["feat", "fix"]
no_period_end = true
```

**Rules:**
- Must follow pattern: `type(scope)?: description` with optional body and footer
- Type must be one of the predefined types
- Scope is optional (unless `scope_required = true`)
- Breaking changes marked with `!` before colon and `BREAKING CHANGE:` in footer
- Description must start with lowercase (configurable with `subject_case`)
- No period at end of description (configurable with `no_period_end`)
- Subject line must not exceed max_subject_length
- Breaking changes only allowed for specified types

## 2. GitHub Style

```toml
[tool.commit_lint]
format_type = "github"
max_subject_length = 72
imperative_mood = true
issue_reference_required = false
keywords = ["Fixes", "Closes", "Resolves"]
```

**Rules:**
- Brief, concise first line (max_subject_length defaults to 72)
- Should use imperative mood in subject line (can be disabled)
- Issue references in format "Fixes #123" use allowed keywords
- Issue references can be required (with `issue_reference_required = true`)
- Optional detailed description after a blank line
- No explicit style rules for the description body

## 3. Jira Style

```toml
[tool.commit_lint]
format_type = "jira"
jira_project_keys = ["PROJ", "TEST"]
require_issue_id = true
max_message_length = 72
```

**Rules:**
- Must start with issue ID like "PROJ-123: Message" (if `require_issue_id = true`)
- Issue ID must match one of the configured project keys
- Message part must not exceed max_message_length
- Optional detailed description after a blank line
- No specific format requirements for the message content itself

## 4. Custom Format

```toml
[tool.commit_lint]
format_type = "custom"
custom_pattern = "^\\[\\w+\\] .+$"  # Example: [CATEGORY] Message
```

**Rules:**
- Must match the provided regex pattern
- In this example, commits must start with a category in square brackets
- The pattern is fully customizable to fit specific team conventions
- No additional validation is performed beyond pattern matching

Each format has its specific validation logic in its respective module and supports interactive message creation that follows these rules.
