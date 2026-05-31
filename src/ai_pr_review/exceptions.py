class AIPrReviewError(Exception):
    code = "AI_PR_REVIEW_ERROR"
    message = "AI PR review error"
    status_code = 500

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.message
        super().__init__(self.detail)


class InvalidPRUrlError(AIPrReviewError):
    code = "INVALID_PR_URL"
    message = "Invalid GitHub PR URL"
    status_code = 400


class GitHubAPIError(AIPrReviewError):
    code = "GITHUB_API_ERROR"
    message = "GitHub API error"
    status_code = 502


class GitHubAuthError(AIPrReviewError):
    code = "GITHUB_AUTH_ERROR"
    message = "GitHub authentication failed"
    status_code = 403


class PullRequestNotFoundError(AIPrReviewError):
    code = "PULL_REQUEST_NOT_FOUND"
    message = "Pull request not found"
    status_code = 404


class AIServiceError(AIPrReviewError):
    code = "AI_SERVICE_ERROR"
    message = "AI service error"
    status_code = 502
