# System Design

## 1. System Goals

AI PR Review Assistant helps teams review GitHub pull requests with a combination of structured GitHub data, deterministic rules, and optional AI analysis.

The main goals are:

- Accept a GitHub PR URL from API or CLI entry points.
- Fetch PR metadata, changed files, patches, and commit messages.
- Build a compact review context that is safe to send to an AI model.
- Detect common risks with rule-based checks before or alongside AI analysis.
- Return consistent API responses and Markdown CLI reports.
- Keep the system modular so GitHub fetching, context construction, AI prompts, and response formatting can evolve independently.

## 2. Overall Architecture

The system is split into small layers:

```text
Client
  -> API or CLI
  -> Review service boundary
  -> GitHub client
  -> Review context builders and rule checks
  -> AI client and prompt loader
  -> Response or Markdown report
```

The API layer is implemented with FastAPI. It exposes health and review routes under `/api`.

The CLI layer uses `argparse` and calls the same review service boundary as the API. It prints a Markdown report and does not publish GitHub comments by default.

The GitHub layer owns URL parsing, REST API calls, and conversion from GitHub JSON into internal dataclasses.

The review layer owns diff context construction, file classification, ignore rules, risk rules, and summary helpers.

The AI layer owns prompt loading and external model calls. It is kept separate so the application can run rule-only or mock flows without requiring AI access.

## 3. Current Directory Structure

```text
AI-PR-Review/
  main.py                         FastAPI application factory and exception handlers
  pyproject.toml                  Package metadata, dependencies, CLI entry point
  README.md                       User-facing setup and usage guide
  docs/
    design.md                     System design documentation
  src/
    ai_pr_review/
      api/                        FastAPI routers
      ai/                         AI client and prompt templates
      github/                     GitHub URL parsing, models, and API client
      review/                     Review helpers, diff context, ignore rules, risk logic
      schemas/                    API request and response models
      utils/                      Shared utilities
      cli.py                      Command-line entry point
      config.py                   Environment-based settings
      exceptions.py               Application exception types
  tests/                          Unit and API tests
```

## 4. GitHub Data Fetch Flow

The GitHub flow starts with a PR URL such as:

```text
https://github.com/owner/repo/pull/123
```

The parser extracts:

- `owner`
- `repo`
- `pull_number`

The `GitHubClient` then uses GitHub REST API endpoints:

- `GET /repos/{owner}/{repo}/pulls/{pull_number}`
- `GET /repos/{owner}/{repo}/pulls/{pull_number}/files`
- `GET /repos/{owner}/{repo}/pulls/{pull_number}/commits`

The client maps GitHub JSON into internal models such as:

- `GitHubPullRequest`
- `GitHubChangedFile`
- `GitHubCommit`

Changed file fetching supports pagination with `per_page=100` and increasing `page` values until a page returns fewer than 100 files. This avoids missing large PRs while still preventing unbounded loops through a maximum page limit.

## 5. AI Analysis Flow

The AI analysis flow is designed to be optional and replaceable:

1. Fetch PR metadata, file changes, and commits.
2. Filter files with built-in skip rules and optional `.aiprignore` patterns.
3. Build diff context with `build_diff_context`.
4. Apply rule-based risk checks.
5. Load prompt templates from `src/ai_pr_review/ai/prompts`.
6. Send compact context to the configured AI provider when enabled.
7. Combine PR metadata, summary, risks, AI summary, and suggestions into the API or CLI response.

Current API and CLI flows can use mock or lightweight service behavior. Real AI calls require service wiring plus model credentials.

## 6. Model Selection Approach

The default model configuration is environment-driven:

```text
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
```

The intended selection strategy is:

- Use a lower-cost model for summaries and low-risk PRs.
- Use a stronger model for complex PRs, security-sensitive changes, or high-risk rule findings.
- Keep prompt templates provider-neutral where possible.
- Isolate AI provider code in `ai/client.py` so model changes do not affect GitHub or API layers.

The project should prefer structured, compact inputs over sending raw repository data. This keeps latency and token usage predictable.

## 7. Context Acquisition

Review context is assembled from several sources:

- PR metadata: title, body, state, author, base branch, head branch, head SHA.
- Changed file metadata: filename, status, additions, deletions, total changes, file URLs.
- Patch content: unified diff patches from GitHub.
- Commit messages: SHA, message, author name, and author email.
- File classification: code, tests, configs, docs, generated files, or other categories.
- Ignore rules: `.aiprignore` patterns such as `dist/`, `generated/`, `*.min.js`, and `package-lock.json`.

Diff context intentionally preserves file path and change statistics even when patches are skipped or truncated. This allows summaries and risk checks to mention affected files without requiring full patch text.

Patch length is controlled by:

```text
MAX_DIFF_CHARS
MAX_PATCH_CHARS_PER_FILE
```

If a patch is truncated, the context includes:

```text
is_truncated=true
```

The truncation strategy keeps the beginning of each patch because it usually contains hunk headers and early changed lines that help orient reviewers.

## 8. False Positive And Missing Finding Controls

The system reduces false positives and missed findings through layered controls:

- Skip binary, generated, lock, vendor, and ignored files before AI analysis.
- Keep file metadata even when patch content is unavailable.
- Use deterministic risk rules for known signals such as sensitive files, large PRs, missing tests, or risky areas.
- Use explicit risk categories and confidence levels for findings.
- Prefer concise AI context to avoid model confusion from very large diffs.
- Return structured errors for invalid PR URLs, GitHub failures, auth failures, missing PRs, and AI failures.

Known exception types include:

- `InvalidPRUrlError`
- `GitHubAPIError`
- `GitHubAuthError`
- `PullRequestNotFoundError`
- `AIServiceError`

API errors use a consistent envelope:

```json
{
  "success": false,
  "message": "Invalid GitHub PR URL",
  "data": null,
  "error": {
    "code": "INVALID_PR_URL",
    "detail": "..."
  }
}
```

## 9. Response Speed Optimization

The main speed controls are:

- Fetch only the required GitHub endpoints for the current flow.
- Use pagination for changed files, but cap maximum pages.
- Skip files that should not be analyzed.
- Limit total diff context size and per-file patch size.
- Reuse prompt templates from disk rather than building prompts dynamically in many places.
- Keep CLI output local and avoid publishing GitHub comments by default.

Future API versions can add async background jobs for large PRs. The current synchronous API is simpler and suitable for small to medium reviews or mocked service flows.

## 10. Future Extensions

Planned extension directions include:

- Implement a full `ReviewService` orchestration layer that combines GitHub fetches, summaries, rules, and AI calls.
- Add asynchronous review jobs for large PRs.
- Add GitHub review comment publishing as an explicit opt-in feature.
- Support richer `.aiprignore` behavior if users need closer `.gitignore` compatibility.
- Add caching for GitHub API responses and prompt outputs.
- Add model routing based on PR size, risk level, and file categories.
- Add structured line-level comments and suggested patches.
- Add repository-level configuration for risk rules and model settings.
- Improve observability with request IDs, latency metrics, and provider error metrics.
- Expand tests around API error mapping, truncation behavior, and end-to-end review flows.
