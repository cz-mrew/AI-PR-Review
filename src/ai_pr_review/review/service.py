from ..github.client import GitHubClient
from ..github.parser import parse_file_change, parse_github_pr_url
from .diff import build_diff_context
from .risk_rules import detect_rule_based_risks
from .summary import generate_rule_based_summary


class ReviewService:
    def __init__(self, github_client: GitHubClient) -> None:
        self._github = github_client

    def review(self, pr_url: str) -> dict:
        parsed = parse_github_pr_url(pr_url)
        owner, repo, pull_number = parsed.owner, parsed.repo, parsed.pull_number

        pr = self._github.get_pull_request(owner, repo, pull_number)
        raw_files = self._github.get_pull_request_files(owner, repo, pull_number)

        file_changes = [
            parse_file_change(
                filename=f.filename,
                status=f.status,
                additions=f.additions,
                deletions=f.deletions,
                changes=f.changes,
                patch=f.patch,
            )
            for f in raw_files
        ]

        diff_context = build_diff_context(file_changes)
        summary = generate_rule_based_summary(file_changes)
        risks = [self._risk_to_dict(r) for r in detect_rule_based_risks(file_changes)]

        return {
            "pr": {
                "title": pr.title,
                "author": pr.user.login,
                "state": pr.state,
                "base_branch": pr.base_branch,
                "head_branch": pr.head_branch,
                "head_sha": pr.head_sha,
                "html_url": pr.html_url,
            },
            "summary": summary,
            "ai_summary": None,
            "risks": risks,
            "review_suggestions": None,
        }

    @staticmethod
    def _risk_to_dict(r) -> dict:
        return {
            "file": r.file,
            "line": r.line,
            "risk_level": r.risk_level.value,
            "source": r.source.value,
            "category": r.category.value,
            "message": r.message,
            "suggestion": r.suggestion,
            "confidence": r.confidence.value,
        }
