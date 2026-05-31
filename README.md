# AI PR Review Assistant

AI PR Review Assistant is a FastAPI-based tool for reviewing GitHub pull requests. It fetches PR metadata, changed files, and commit information, then exposes review results through an HTTP API and a command-line interface.

The current implementation is designed as a foundation for rule-based and AI-assisted PR analysis. Some service methods are intentionally lightweight and can be replaced with real GitHub and AI integrations as the project evolves.

## Features

- Parse GitHub pull request URLs.
- Fetch pull request metadata from GitHub.
- Fetch changed files, including paginated file lists.
- Fetch PR commit messages.
- Build structured diff context with patch length limits.
- Support simple `.aiprignore` file matching.
- Expose health and review API endpoints.
- Provide a CLI command that prints a Markdown review report.
- Return structured API error responses for known failures.

## Directory Structure

```text
AI-PR-Review/
  main.py
  pyproject.toml
  README.md
  src/
    ai_pr_review/
      ai/
      api/
      github/
      review/
      schemas/
      utils/
      cli.py
      config.py
      exceptions.py
  tests/
```

## Installation

Use Python 3.10 or newer.

```bash
python -m venv .venv
```

On Windows PowerShell:

```bash
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Install the project in editable mode:

```bash
python -m pip install -e .
```

Run tests:

```bash
python -m pytest
```

## Environment Variables

Configuration is loaded from environment variables and an optional `.env` file.

```text
APP_NAME=AI PR Review Assistant
APP_ENV=development
GITHUB_TOKEN=
LLM_PROVIDER=openai
LLM_API_KEY=
LLM_MODEL=gpt-4o-mini
REQUEST_TIMEOUT=30
MAX_DIFF_CHARS=120000
MAX_PATCH_CHARS_PER_FILE=20000
```

`GITHUB_TOKEN` is optional for public repositories, but GitHub rate limits are lower without it.

## Start The API Server

```bash
python -m uvicorn main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

## Health Check

```bash
curl http://127.0.0.1:8000/api/health
```

Example response:

```json
{
  "success": true,
  "message": "AI PR Review Assistant is running.",
  "data": {
    "status": "ok",
    "app_env": "development"
  },
  "error": null
}
```

## Review API

Call `POST /api/review` with a GitHub PR URL:

```bash
curl -X POST http://127.0.0.1:8000/api/review \
  -H "Content-Type: application/json" \
  -d "{\"pr_url\":\"https://github.com/owner/repo/pull/123\"}"
```

Example response shape:

```json
{
  "success": true,
  "message": "PR review completed.",
  "data": {
    "pr": {
      "url": "https://github.com/owner/repo/pull/123"
    },
    "summary": {},
    "ai_summary": null,
    "risks": [],
    "review_suggestions": null
  },
  "error": null
}
```

Known errors use the same response envelope:

```json
{
  "success": false,
  "message": "Invalid GitHub PR URL",
  "data": null,
  "error": {
    "code": "INVALID_PR_URL",
    "detail": "Unsupported PR URL"
  }
}
```

## CLI Usage

After installing the project, run:

```bash
ai-pr-review review https://github.com/owner/repo/pull/123
```

The CLI prints a Markdown report to stdout:

```markdown
# PR Review Report

## PR
- **url**: https://github.com/owner/repo/pull/123

## Summary
- No summary available.

## AI Summary
No AI summary available.

## Risks
- No risks found.

## Review Suggestions
No review suggestions available.
```

The CLI does not publish GitHub review comments by default.

## Ignore Rules

Create a `.aiprignore` file to skip files or directories during analysis. See `.aiprignore.example`.

Supported simple patterns include:

```text
dist/
generated/
*.min.js
package-lock.json
```

Full `.gitignore` compatibility is not currently required or implemented.

## Current Limitations

- `/api/review` currently uses a lightweight review service implementation.
- Real AI analysis may require additional service wiring and `LLM_API_KEY`.
- GitHub API access for private repositories requires `GITHUB_TOKEN`.
- Ignore rules intentionally support only simple directory, filename, and wildcard patterns.
- CLI output is local Markdown only and does not publish comments to GitHub.
- Large diff patches are truncated according to `MAX_DIFF_CHARS` and `MAX_PATCH_CHARS_PER_FILE`.
